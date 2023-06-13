"""
    @file main.py
    @author Derek Tan
"""

import atexit
import time
import socket

import http1.request as req
import http1.scanner as reqstream
import http1.sender as res

import utils.rescache as rescache

import handlers.handcache as hdlrstore

SERVER_APP_NAME = "Tippy/v0.1"

SERVER_ST_IDLE = 0
SERVER_ST_REQUEST = 1
SERVER_ST_REPLY = 2
SERVER_ST_ERR_REQ = 3
SERVER_ST_ERR_GEN = 4
SERVER_ST_STOP = 5

SERVER_MAX_STRIKE_LIMIT = 2

class TippyServer:
    """
        @description The main server class. Contains main service logic following a finite state machine to handle requests, send responses, and possibly repeat or end.
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
    
    def force_stop(self):
        """
            @description Stops the server from continuing its next service.
        """
        self.serve_state = SERVER_ST_STOP
        self.socket.close()
    
    def register_handler(self, paths: list[str], handler = None):
        return self.handler_storage.add_handler(paths, handler)
    
    def get_time_str(self):
        """
            @description Makes a GMT time string for all responses. This is a helper method!
        """
        # Get raw time!
        now = time.gmtime()
        secs = now.tm_sec
        secs_str = None

        # NOTE: python time structs use leap seconds up to 61s, so I must normalize them in 0 to 59s ranges!
        if secs > 59:
            secs = secs % 60

        if secs < 10:
            secs_str = f'0{secs}'
        else:
            secs_str = f'{secs}'

        return time.strftime("%a, %d %b %Y %H:%M:") + f'{secs_str} GMT'

    def reply_error(self, request: req.SimpleRequest, optional_stat: str):
        """
            @description Generates a dummy error response.
        """
        write_ok = self.to_client.send_heading(optional_stat)
        
        # NOTE: Check for remote endpoint close (send 0) since we need to gracefully handle non-persistent clients.
        if not write_ok:
            return SERVER_ST_STOP

        self.to_client.send_header("Date", self.get_time_str())
        self.to_client.send_header("Connection", "Keep-Alive")
        self.to_client.send_header("Server", self.appname)
        self.to_client.send_body(res.RES_ERR_BODY, "*/*", None)
        
        # NOTE: respect connection closing headers for graceful ending of HTTP exchange.
        if request.before_close():
            return SERVER_ST_STOP

        return SERVER_ST_REQUEST

    def reply_normal(self, request: req.SimpleRequest):
        """
            @description Dummy response helper for now. Sends \"Hello World!\" at '/' to the client.
        """
        request_method_ok = request.method_supported()
        
        if not request_method_ok:
            return self.reply_error(request, "501")
        
        request_last = request.before_close()

        temp_handler_ref = self.handler_storage.get_handler(request.path)

        if temp_handler_ref is None:
            return self.reply_error(request, "404")
        
        if not temp_handler_ref(self.resource_storage, self.get_time_str, request, self.to_client):
            return SERVER_ST_STOP

        # NOTE: Respect connection closing header for graceful handle of 1-time client msg.
        if request_last:
            return SERVER_ST_STOP
        
        return SERVER_ST_REQUEST

    def run(self):
        """
            @description Listens for a client connection before serving it.
        """
        # 1. connect client!
        self.conn_socket, client_addr = self.socket.accept()

        # 2. setup request & response streams!
        self.from_client = reqstream.HttpScanner(self.conn_socket.makefile(mode="r"))
        self.to_client = res.SimpleSender(self.conn_socket.makefile("wb"))
        request = None

        # 3. serve content with FSM!
        while self.serve_state != SERVER_ST_STOP and self.strikes <= SERVER_MAX_STRIKE_LIMIT:
            print(f'serve_state = {self.serve_state}')  # DEBUG!

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
                    self.serve_state = self.reply_normal(request)
                elif self.serve_state == SERVER_ST_ERR_REQ:
                    self.serve_state = self.reply_error(request, "400")
                elif self.serve_state == SERVER_ST_ERR_GEN:
                    self.serve_state = self.reply_error(request, "500")
                else:
                    # Do not continue on any invalid state to not send invalid responses!
                    self.serve_state = SERVER_ST_STOP
            except Exception as server_err:
                self.strikes += 1
                print(f'Server Err: {server_err}')
                self.serve_state = SERVER_ST_ERR_GEN
        
        # NOTE: End persistent connection and cleanup to free resources. 
        self.socket.close()

my_server = None

# HANDLERS

def handle_index(context: rescache.ResourceCache, time_generator: any, request: req.SimpleRequest, response: res.SimpleSender):
    temp_resource = context.get_item("index.html")
    
    response.send_heading("200")
    response.send_header("Date", time_generator())
    response.send_header("Connection", "Keep-Alive")
    response.send_header("Server", SERVER_APP_NAME)

    if request.method == "HEAD":
        return response.send_body(res.RES_HEAD_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())
    else:
        return response.send_body(res.RES_GET_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())

def handle_info(context: rescache.ResourceCache, time_generator: any, request: req.SimpleRequest, response: res.SimpleSender):
    temp_resource = context.get_item("info.html")

    response.send_heading("200")
    response.send_header("Date", time_generator())
    response.send_header("Connection", "Keep-Alive")
    response.send_header("Server", SERVER_APP_NAME)

    if request.method == "HEAD":
        return response.send_body(res.RES_HEAD_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())
    else:
        return response.send_body(res.RES_GET_BODY, temp_resource.get_mime_type(), temp_resource.as_bytes())

def interrupt_handler():
    my_server.force_stop()
    print("Stopped server.")

# DRIVER CODE

atexit.register(interrupt_handler)

my_server = TippyServer()

my_server.register_handler(["/", "/index.html"], handle_index)
my_server.register_handler(["/info.html"], handle_info)

my_server.run()
