import json
import os
from pathlib import Path
from typing import TypedDict

APP_PATH = Path(__file__).resolve().parent
PROJECT_PATH = APP_PATH.parent
BASE_PATH = Path(os.getenv('BASE_PATH', PROJECT_PATH))

CONFIG_PATH = BASE_PATH / 'config'
DATA_PATH = BASE_PATH / 'data'

CONFIG_PATH.mkdir(parents=True, exist_ok=True)
DATA_PATH.mkdir(parents=True, exist_ok=True)

ENV_PATHS = [
    BASE_PATH / '.env',
    BASE_PATH / '.env.local',
    CONFIG_PATH / '.env',
    CONFIG_PATH / '.env.local',
]

for env_path in ENV_PATHS:
    if env_path and env_path.exists() and env_path.is_file():
        from dotenv import load_dotenv

        load_dotenv(env_path)
        # print(f"Loaded env from {env_path}")
        break
# else:
#     print("No .env file found")


# Localizations
LOCALE_PATH = PROJECT_PATH / 'locale'
DEFAULT_LOCALE = os.getenv('DEFAULT_LOCALE', 'en')
DOMAIN = os.getenv('LOCALE_DOMAIN', 'messages')

CONTACTS_PATH = Path(os.getenv('CONTACTS_PATH', CONFIG_PATH / 'contacts.json'))
_CONTACT = TypedDict('_CONTACT', {
    'type': str,
    'link': str,
    'name': str,
})

CONTACTS: list[_CONTACT] = []

if CONTACTS_PATH.exists():
    with open(CONTACTS_PATH, 'r') as f:
        CONTACTS = json.load(f)
