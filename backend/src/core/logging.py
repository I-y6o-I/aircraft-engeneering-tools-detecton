import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging():
    """Basic JSON-ish console logging + optional file rotation."""

    fmt = '%(asctime)s %(levelname)s %(name)s %(message)s'
    datefmt = '%Y-%m-%dT%H:%M:%S%z'

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    root.addHandler(ch)

    # Reduce noise from urllib/uvicorn access if needed:
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
