"""
    instance.py\n
    Rewritten driver class for my HTTP/1.1 server, Tippy.\n
    Derek Tan
"""

from time import sleep
from queue import Queue
from threading import Event, Thread, current_thread

from core.producer import ConnProducer, producer_runnable
from core.worker import ConnWorker, worker_runnable

from utils.rescache import ResourceCache
from handlers.handcache import HandlerCache
from handlers.ctx.context import HandlerCtx

TIPPY_VERSION_STRING = "Tippy/v0.5"
TIPPY_DEFAULT_HOST_NAME = "localhost"
TIPPY_DEFAULT_HOST_PORT = 8085
TIPPY_DEFAULT_BACKLOG = 5
TIPPY_DEFAULT_WWW_DIR = "./public"
TIPPY_WORKER_COUNT = 2
TIPPY_WORKER_NAME = 'tipster'

class Tippy:
    def __init__(self, server_name: str = TIPPY_VERSION_STRING, host_name: str = TIPPY_DEFAULT_HOST_NAME, host_port: int = TIPPY_DEFAULT_HOST_PORT, backlog:int = TIPPY_DEFAULT_BACKLOG, public_folder: str = TIPPY_DEFAULT_WWW_DIR):
        # Server data #
        self.server_name = server_name
        self.host_name = f'{host_name}:{host_port}'
        self.resources = ResourceCache(public_folder)
        self.handlers = HandlerCache()
        self.context = HandlerCtx(self.resources)

        # Server concurrency #
        self.shared_queue = Queue(backlog)
        self.shared_eventer = Event()

        self.producer = ConnProducer((host_name, host_port), backlog)
        self.workers: list[ConnWorker] = []

        self.producer_thread = Thread(
            target=producer_runnable,
            name=f'top_{TIPPY_WORKER_NAME}',
            args=(self.producer, self.shared_queue, self.shared_eventer)
        )
        self.worker_threads: list[Thread] = []

        # Latent thread creation... #
        for i in range(0, TIPPY_WORKER_COUNT):
            self.workers.append(ConnWorker(i, self.server_name, self.host_name, self.context, self.handlers))
        
        for thread_n in range(0, TIPPY_WORKER_COUNT):
            self.worker_threads.append(
                Thread(
                    target=worker_runnable, name=f'{TIPPY_WORKER_NAME}{thread_n}',
                    args=(self.workers[thread_n], self.shared_queue, self.shared_eventer)
                )
            )
    
    def set_handler(self, routes: list[str] = None, callback = None):
        return self.handlers.add_handler(routes, callback) and self.resources.add_item_paths(routes)
    
    def set_fallback_handler(self, fallback = None):
        self.handlers.set_fallback_handler(fallback)

    def run_service(self):
        # TODO Implement with 1 producer and n workers. Default to 2 workers.
        # 1. Launch producer before workers.
        self.producer_thread.start()

        sleep(0.010)

        # 2. Enjoy watching it serve your browser. :)
        for worker_thread in self.worker_threads:
            worker_thread.start()
    
    def stop_service(self):
        self.producer.soft_stop()

        for worker in self.workers:
            worker.cleanup()
