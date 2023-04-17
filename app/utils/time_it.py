import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

__all__ = ("timeit",)


@contextmanager
def timeit(name: str = "Timeit", log: logging.Logger = logger):
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        log.info("%s: %.4fs.", name, end - start)
