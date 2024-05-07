import logging.config
import os
from datetime import datetime, tzinfo
from pathlib import Path

import pytz

from .fmt_logger import FmtFormatter
from .json_logger import JsonFormatter
from .paths import LOG_PATH
from .settings import settings

__all__ = ("init_logger_config",)


def init_logger_config(log_path: Path, time_zone: tzinfo = pytz.timezone("Europe/Moscow")) -> None:
    log_filename = datetime.now(time_zone).strftime("_%Y-%m-%d-%H-%M-%S.jsonl")
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": FmtFormatter,
                "fmt_dict": {
                    "timestamp": "asctime",
                    "level": "levelname",
                    "loggerName": "name",
                    "message": "message",
                },
            },
            "json": {
                "()": JsonFormatter,
                "fmt_dict": {
                    "timestamp": "asctime",
                    "level": "levelname",
                    "loggerName": "name",
                    "message": "message",
                },
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "info_file_handler": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": log_path / f"info{log_filename}",
                "mode": "w",
                "maxBytes": 10485760,
                "backupCount": 40,
                "encoding": "utf8",
            },
            "error_file_handler": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": log_path / f"errors{log_filename}",
                "mode": "w",
                "maxBytes": 10485760,
                "backupCount": 40,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "": {
                "level": logging.DEBUG if os.getenv("DEBUG") else logging.INFO,
                "handlers": ["console"],
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "info_file_handler", "error_file_handler"],
        },
    }

    if os.getenv("DISABLE_LOG"):
        logging.disable()
    elif os.getenv("CLI_MODE"):
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        logging.config.dictConfig(config)


# Load custom logger config
init_logger_config(LOG_PATH, settings.time_zone)
logging.getLogger("httpx").setLevel(level=logging.ERROR)
