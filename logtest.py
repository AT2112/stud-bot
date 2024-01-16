import logging
import threading

def log():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    thread_logger = logging.getLogger(threading.current_thread().name)
    thread_logger.setLevel(logging.DEBUG)

