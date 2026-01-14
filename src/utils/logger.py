"""Logging setup."""

from __future__ import annotations

import logging
import os
import pathlib
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(level: str = "INFO", logfile: str | None = None) -> None:
    """Configure root logger with stdout + optional rotating file handler.

    Log level can be overridden via LOG_LEVEL env var.
    File output can be enabled via LOG_FILE env var or the logfile argument.
    """
    log_level = os.getenv("LOG_LEVEL", level).upper()
    log_file_path = os.getenv("LOG_FILE", logfile)
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file_path:
        path = pathlib.Path(log_file_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3))
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=handlers,
    )
