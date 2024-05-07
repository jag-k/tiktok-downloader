import os
from pathlib import Path

__all__ = (
    "APP_PATH",
    "PROJECT_PATH",
    "BASE_PATH",
    "DATA_PATH",
    "LOG_PATH",
    "CONFIG_PATH",
    "LOCALE_PATH",
)

APP_PATH = Path(__file__).resolve().parent.parent
PROJECT_PATH = APP_PATH.parent
BASE_PATH = Path(os.getenv("BASE_PATH", PROJECT_PATH))

DATA_PATH = BASE_PATH / "data"
LOG_PATH = DATA_PATH / "logs"
CONFIG_PATH = BASE_PATH / "config"
LOCALE_PATH = PROJECT_PATH / "locales"

DATA_PATH.mkdir(parents=True, exist_ok=True)
LOG_PATH.mkdir(parents=True, exist_ok=True)
CONFIG_PATH.mkdir(parents=True, exist_ok=True)
