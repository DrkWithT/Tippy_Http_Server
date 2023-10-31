"""
    @file producer.py\n
    @description Contains logic for a producing worker thread getting pending client connections for a worker pool to handle.\n
    @author Derek Tan
"""

from threading import Event
from queue import Queue, Full
from socket import create_server, socket

class ConnProducer:
    def __init__(self, address_tuple: tuple[str, int], backlog_len: int) -> None:
        if backlog_len < 1:
            raise ValueError(f'{__name__}: Invalid socket backlog {backlog_len}')

        self.server_socket = create_server(address=address_tuple, backlog=backlog_len)
        self.is_listening = False
    
    def run(self, queue_ref: Queue, event_ref: Event):
        while self.is_listening:
            try:
                # First, listen for a new connection request...
                connection_info = self.server_socket.accept()

                # Tell workers to wait until a work item is placed.
                event_ref.clear()

                # Try to put the connection as a new task tuple on the queue. Wait until the queue has space.
                queue_ref.put(item=connection_info, block=True)
            except Full as queue_error:
                connection_info[0].close()
                print(f'{__name__}: Failed to queue client connection with error: {queue_error}')
            finally:
                # Tell workers that a task is placed for them.
                event_ref.set()
        
        queue_ref.join()
    
    def soft_stop(self):
        self.is_listening = False
        self.server_socket.close()

def producer_runnable(producer_ref: ConnProducer, queue_ref: Queue, event_ref: Event):
    producer_ref.run(queue_ref, event_ref)
    print(f'Stopped producer.')
