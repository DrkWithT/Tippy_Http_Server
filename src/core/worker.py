"""
    @file worker.py\n
    @description Contains an encapsulated piece of logic to handle lower level request-response actions of the server.\n
    @author Derek Tan
"""

from calendar import timegm
from time import gmtime
from threading import Event
from socket import socket
from queue import Queue

from http1.request import SimpleRequest
from http1.scanner import HttpScanner
from http1.sender import SimpleSender, RES_ERR_BODY
from handlers.ctx.context import HandlerCtx
from handlers.handcache import HandlerCache

WORKER_ST_IDLE = 0
WORKER_ST_CONSUME = 1
WORKER_ST_RECV = 2
WORKER_ST_HANDLE = 3
WORKER_ST_REDO = 4
WORKER_ST_ERROR = 5
WORKER_ST_RESET = 6
WORKER_ST_END = 7

class ConnWorker:
    def __init__(self, _id: int, server_name: str, host_name: str, worker_context: HandlerCtx, handlers: HandlerCache) -> None:
        self.id = _id
        self.state = WORKER_ST_IDLE
        self.server_name = server_name
        self.host_name = host_name
        self.current_socket = None
        self.scanner = None
        self.sender = None
        self.temp_request = None
        self.handlers = handlers
        self.context = worker_context
    
    def should_send_update(self):
        resource_ref = self.context.get_resource(self.temp_request.path)

        # Check if the resource exists to be checked by caching time.
        if resource_ref is None:
            return False
        
        # Compute if the resource hits the cache by time diffs.
        resource_modify_time = resource_ref.get_modify_date()
        resource_need_time = timegm(gmtime())

        return resource_modify_time < resource_need_time

    def do_consume(self, queue_ref: Queue[tuple], event_ref: Event):
        print(f'{__name__}: Worker {self.id} awaiting work.')

        # Wait for the producer to signal that work is available...
        event_ref.wait()

        print(f'{__name__}: Worker {self.id} woke up.')

        # Get the work item.
        client_sock, client_addr = queue_ref.get()

        self.current_socket = client_sock
        self.scanner = HttpScanner(self.current_socket.makefile('r'))
        self.sender = SimpleSender(self.current_socket.makefile('wb'))

        print(f'{__name__}@worker {self.id}: Consumed client connection with {client_addr}')

        queue_ref.task_done()

        return WORKER_ST_RECV

    def do_recieve(self):
        self.temp_request = self.scanner.next_request()

        return WORKER_ST_HANDLE
    
    def do_handle(self):
        # Validate all important headers I can to check which requests are malformed.
        if self.temp_request.get_header("host") is not None:
            return self.do_good_handle()
        
        # Send error replies on malformed HTTP/1.1 responses: deal with lack of 'Host: ...' for now.
        return self.do_bad_handle()
    
    def do_good_handle(self):
        req_method_ok = self.temp_request.method_supported()

        if not req_method_ok:
            return self.do_bad_handle("501")
        
        if not self.should_send_update():
            return self.do_bad_handle("304")
        
        req_is_last = self.temp_request.before_close()

        handler_ref = self.handlers.get_handler(self.temp_request.path)

        # NOTE handlers only fail on bad I/O operations... Reset connection in this case too so no malformed replies are sent back easily.
        if not handler_ref(self.context, self.temp_request, self.sender) or req_is_last:
            return WORKER_ST_RESET

        return WORKER_ST_REDO

    def do_bad_handle(self, http_status: str):
        error_reply_top_ok = self.sender.send_heading(http_status)

        # A write error likely means the connection is poor or dead... Reset the socket to encourage a reconnect.
        if not error_reply_top_ok:
            return WORKER_ST_RESET
        
        # Send common headers before 'Connection' header for cleaner control flow.
        self.sender.send_header("Date", self.context.get_gmt_str())
        self.sender.send_header("Server", self.server_name)
        
        # Also respect client wishes to close the connection for protocol courtesy.
        if self.temp_request.before_close():
            self.sender.send_header("Connection", "Close")
        else:
            self.sender.send_header("Connection", "Keep-Alive")
        
        self.sender.send_body(RES_ERR_BODY, "*/*", None)

        return WORKER_ST_REDO
    
    def do_redo(self):
        self.scanner.reset()

        return WORKER_ST_RECV
    
    def do_reset(self):
        self.current_socket.close()
        self.scanner.reset()
        self.scanner = None
        self.sender = None

        return WORKER_ST_CONSUME

    def cleanup(self):
        self.state = WORKER_ST_END

        if self.current_socket is not None:
            self.current_socket.close()

        self.scanner = None
        self.sender = None
        self.handlers = None
        self.context = None
        print(f'{__name__}: Stopped worker {self.id}')

    def do_next(self, queue_ref: Queue[tuple], event_ref: Event):
        if self.state == WORKER_ST_IDLE:
            return WORKER_ST_CONSUME
        elif self.state == WORKER_ST_CONSUME:
            return self.do_consume(queue_ref, event_ref)
        elif self.state == WORKER_ST_RECV:
            return self.do_recieve()
        elif self.state == WORKER_ST_HANDLE:
            return self.do_handle()
        elif self.state == WORKER_ST_REDO:
            return self.do_redo()
        elif self.state == WORKER_ST_RESET:
            return self.do_reset()
        elif self.state == WORKER_ST_ERROR:
            return self.do_reset()
        else:
            # Final case: treat WORKER_ST_END or unknown states as stop codes.
            return WORKER_ST_END

    def run(self, queue_ref: Queue[tuple], event_ref: Event):
        while self.state != WORKER_ST_END:
            try:
                self.state = self.do_next(queue_ref, event_ref)
            except Exception as serve_error:
                print(f'{__name__}: Worker error: {serve_error}')
                self.state = WORKER_ST_ERROR

def worker_runnable(worker_ref: ConnWorker, queue_ref: Queue[tuple], event_ref: Event):
    worker_ref.run(queue_ref, event_ref)
