"""
    @file driver.py
    @author Derek Tan
"""

import socket

import http1.request as req
import http1.scanner as reqstream
import http1.sender as res

import utils.rescache as rescache
import handlers.handcache as hdlrstore
import handlers.ctx.context as context

SERVER_APP_NAME = "Tippy/v0.3"

SERVER_ST_IDLE = 0
SERVER_ST_REQUEST = 1
SERVER_ST_REPLY = 2
SERVER_ST_ERR_REQ = 3
SERVER_ST_ERR_GEN = 4
SERVER_ST_STOP = 5

SERVER_MAX_STRIKE_LIMIT = 2

class TippyServer:
    """
        @description The main server class. Contains main service logic as a finite state machine to process requests, send responses, and continue.
    """

    def __init__(self, hostname="localhost", port=8080, backlog=5, public_folder="./public"):
        """
            @description Initializes the "Tippy" HTTP server. Default args are `hostname=localhost`, `port=8080`, and `backlog=5`. 
        """
        self.appname = SERVER_APP_NAME
        self.fullhost = f'{hostname}:{port}'
        self.backlog = backlog
        self.serve_state = 0
        self.strikes = 0

        self.socket = socket.create_server(address=(hostname, port), backlog=self.backlog)
        self.conn_socket = None
        self.from_client = None
        self.to_client = None

        self.resource_storage = rescache.ResourceCache(public_folder)
        self.handler_storage = hdlrstore.HandlerCache()
        self.context = context.HandlerCtx(self.resource_storage)

    def force_stop(self):
        """
            @description Stops the server from continuing its next service.
        """
        self.serve_state = SERVER_ST_STOP
        self.socket.close()

    def register_handler(self, paths: list[str], handler = None):
        return self.handler_storage.add_handler(paths, handler) and self.resource_storage.add_item_paths(paths)

    def register_fallback_handler(self, handler = None):
        self.handler_storage.set_fallback_handler(handler)

    def should_send_update(self, request: req.SimpleRequest):
        """
            @description Checks if a requested resource is up to date.
        """
        resource_ref = self.resource_storage.get_item(request.path)

        # NOTE: Do not 304 for unknown resources, as this may confuse the user about the message semantics.
        if resource_ref is None:
            return False

        resource_mod_date = resource_ref.get_modify_date()

        request_cache_date = request.get_check_modify_date()

        return resource_mod_date > request_cache_date

    def reply_error(self, request: req.SimpleRequest, optional_stat: str):
        """
            @description Generates a dummy error response.
        """
        write_ok = self.to_client.send_heading(optional_stat)
        
        # NOTE: Check for remote endpoint close (send 0) since we need to gracefully handle non-persistent clients.
        if not write_ok:
            return SERVER_ST_STOP
        
        # NOTE: respect connection closing headers for graceful ending of HTTP exchange.
        if request.before_close():
            self.to_client.send_header("Date", self.context.get_gmt_str())
            self.to_client.send_header("Connection", "Close")
            self.to_client.send_header("Server", self.appname)
            self.to_client.send_body(res.RES_ERR_BODY, "*/*", None)
            return SERVER_ST_STOP
        else:
            self.to_client.send_header("Date", self.context.get_gmt_str())
            self.to_client.send_header("Connection", "Keep-Alive")
            self.to_client.send_header("Server", self.appname)
            self.to_client.send_body(res.RES_ERR_BODY, "*/*", None)

        return SERVER_ST_REQUEST

    def reply_cache_hit(self, request: req.SimpleRequest):        
        write_ok = self.to_client.send_heading("304")

        if not write_ok:
            return SERVER_ST_STOP

        if request.before_close():
            self.to_client.send_header("Date", self.context.get_gmt_str())
            self.to_client.send_header("Connection", "Close")
            self.to_client.send_header("Server", self.appname)
            self.to_client.send_body(res.RES_ERR_BODY, "*/*", None)
            return SERVER_ST_STOP
        else:
            self.to_client.send_header("Date", self.context.get_gmt_str())
            self.to_client.send_header("Connection", "Keep-Alive")
            self.to_client.send_header("Server", self.appname)
            self.to_client.send_body(res.RES_ERR_BODY, "*/*", None)

        return SERVER_ST_REQUEST

    def reply_normal(self, request: req.SimpleRequest):
        """
            @description Dummy response helper for now. Sends \"Hello World!\" at '/' to the client.
        """
        request_method_ok = request.method_supported()

        if not request_method_ok:
            return self.reply_error(request, "501")

        if not self.should_send_update(request):
            return self.reply_cache_hit(request)

        request_last = request.before_close()

        temp_handler_ref = self.handler_storage.get_handler(request.path)

        if not temp_handler_ref(self.context, request, self.to_client):
            return SERVER_ST_STOP

        # NOTE: Respect connection closing header for graceful handle of final client msg... Maybe I should later send Connection: Close?
        if request_last:
            return SERVER_ST_STOP

        return SERVER_ST_REQUEST

    def run(self):
        """
            @description Listens for a client connection before serving it.
        """
        print(f'Running on {self.fullhost}')

        # 1. connect client!
        self.conn_socket, client_addr = self.socket.accept()

        # 2. setup request & response streams!
        self.from_client = reqstream.HttpScanner(self.conn_socket.makefile(mode="r"))
        self.to_client = res.SimpleSender(self.conn_socket.makefile("wb"))
        request = None

        # 3. serve content with FSM!
        while self.serve_state != SERVER_ST_STOP and self.strikes <= SERVER_MAX_STRIKE_LIMIT:
            try:
                if self.serve_state == SERVER_ST_IDLE:
                    # Start State!
                    self.serve_state = SERVER_ST_REQUEST
                elif self.serve_state == SERVER_ST_REQUEST:
                    # Read request!
                    request = self.from_client.next_request()
                    self.from_client.reset()

                    # Check Host header!
                    if request.get_header("host") == self.fullhost:
                        self.serve_state = SERVER_ST_REPLY
                    else:
                        self.serve_state = SERVER_ST_ERR_REQ
                elif self.serve_state == SERVER_ST_REPLY:
                    # Try replying normally!
                    self.serve_state = self.reply_normal(request)
                elif self.serve_state == SERVER_ST_ERR_REQ:
                    # Try to reply an error message!
                    self.serve_state = self.reply_error(request, "400")
                elif self.serve_state == SERVER_ST_ERR_GEN:
                    self.serve_state = self.reply_error(request, "500")
                else:
                    # Do not continue on any invalid state to not send invalid responses!
                    self.serve_state = SERVER_ST_STOP
            except Exception as server_err:
                self.strikes += 1
                print(f'Server Err: {server_err.with_traceback(server_err)}')
                self.serve_state = SERVER_ST_ERR_GEN
        
        # NOTE: End connection and cleanup. 
        self.socket.close()
