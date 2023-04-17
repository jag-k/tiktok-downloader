import json
import os
import sys
from pathlib import Path

import pytz

from app.constants.init_logger import init_logger_config
from app.constants.json_logger import CONTEXT_VARS
from app.constants.load_envs import load_envs
from app.constants.types import *

# region Base paths
APP_PATH = Path(__file__).resolve().parent.parent
PROJECT_PATH = APP_PATH.parent
BASE_PATH = Path(os.getenv("BASE_PATH", PROJECT_PATH))

CONFIG_PATH = BASE_PATH / "config"
DATA_PATH = BASE_PATH / "data"
LOG_PATH = DATA_PATH / "logs"

CONFIG_PATH.mkdir(parents=True, exist_ok=True)
DATA_PATH.mkdir(parents=True, exist_ok=True)
LOG_PATH.mkdir(parents=True, exist_ok=True)
# endregion

# Load envs
load_envs(BASE_PATH, CONFIG_PATH)

# region Localizations
LOCALE_PATH = PROJECT_PATH / "locales"
DEFAULT_LOCALE = os.getenv("DEFAULT_LOCALE", "en")
DOMAIN = os.getenv("LOCALE_DOMAIN", "messages")
# endregion

# region Other
TOKEN = os.getenv("TG_TOKEN")  # Telegram token
TIME_ZONE = pytz.timezone(os.getenv("TZ", "Europe/Moscow"))

# Contacts for help command
CONTACTS_PATH = Path(os.getenv("CONTACTS_PATH", CONFIG_PATH / "contacts.json"))
REPORT_PATH = Path(os.getenv("REPORT_PATH", CONFIG_PATH / "report.json"))
NOTIFY_PATH = Path(os.getenv("NOTIFY_PATH", CONFIG_PATH / "notify.json"))

if not REPORT_PATH.parent.exists():
    REPORT_PATH.parent.mkdir(parents=True)

CONTACTS: list[CONTACT] = []

if CONTACTS_PATH.exists():
    with open(CONTACTS_PATH) as f:
        CONTACTS = json.load(f)

# Telegram file limit
TG_FILE_LIMIT = 50 * 1024 * 1024  # 20 MB

# region MongoDB support
# mongodb://user:password@localhost:27017/database
# mongodb://user:password@localhost:27017/
MONGO_URL = os.getenv("MONGO_URL", None)
MONGO_DB = os.getenv("MONGO_DB", None)

ENABLE_MONGO = MONGO_URL and MONGO_DB
if not ENABLE_MONGO:
    print(
        "Bot requires MongoDB to work.\n"
        "Please, set MONGO_URL and MONGO_DB envs.",
        file=sys.stderr,
    )
    exit(1)
# endregion

# Load custom logger config
init_logger_config(LOG_PATH, TIME_ZONE)
