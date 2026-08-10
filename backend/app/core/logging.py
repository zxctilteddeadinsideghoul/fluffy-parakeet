"""Application-wide logging setup: structured traces to stdout."""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger with a single stdout handler and timestamped lines."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)