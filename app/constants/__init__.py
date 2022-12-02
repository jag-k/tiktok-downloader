import json
import os
from pathlib import Path
from typing import TypedDict

import pytz

from app.constants.init_logger import init_logger_config
from app.constants.load_envs import load_envs

# region Types
_CONTACT = TypedDict('_CONTACT', {
    'type': str,
    'text': str,
    'url': str,
})
# endregion

# region Base paths
APP_PATH = Path(__file__).resolve().parent.parent
PROJECT_PATH = APP_PATH.parent
BASE_PATH = Path(os.getenv('BASE_PATH', PROJECT_PATH))

CONFIG_PATH = BASE_PATH / 'config'
DATA_PATH = BASE_PATH / 'data'
LOG_PATH = DATA_PATH / 'logs'

CONFIG_PATH.mkdir(parents=True, exist_ok=True)
DATA_PATH.mkdir(parents=True, exist_ok=True)
LOG_PATH.mkdir(parents=True, exist_ok=True)
# endregion

# Load envs
load_envs(BASE_PATH, CONFIG_PATH)

# region Localizations
LOCALE_PATH = PROJECT_PATH / 'locales'
DEFAULT_LOCALE = os.getenv('DEFAULT_LOCALE', 'en')
DOMAIN = os.getenv('LOCALE_DOMAIN', 'messages')
# endregion

# region Other
TOKEN = os.getenv("TG_TOKEN")  # Telegram token
TIME_ZONE = pytz.timezone(os.getenv('TZ', 'Europe/Moscow'))

# Contacts for help command
CONTACTS_PATH = Path(os.getenv('CONTACTS_PATH', CONFIG_PATH / 'contacts.json'))

CONTACTS: list[_CONTACT] = []

if CONTACTS_PATH.exists():
    with open(CONTACTS_PATH, 'r') as f:
        CONTACTS = json.load(f)

# Telegram file limit
TG_FILE_LIMIT = 20 * 1024 * 1024  # 20 MB
# endregion

# Load custom logger config
init_logger_config(LOG_PATH, TIME_ZONE)
