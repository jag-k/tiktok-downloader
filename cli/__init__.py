# flake8: noqa: E402

import argparse
import os

os.putenv("CLI_MODE", "1")

from app.constants import DEFAULT_LOCALE
from cli.compile import main as compile_locale
from cli.extract import main as extract_locale
from cli.update import main as update_locale

parser = argparse.ArgumentParser(description="Manage translations")

parser.add_argument(
    "command",
    choices=["extract", "compile", "update", "full_update"],
    help="Command to run",
)

parser.add_argument("-l", "--lang", default="ru")


def full_update_locale(lang: str = DEFAULT_LOCALE):
    extract_locale()
    update_locale(lang)


def main():
    n = parser.parse_args()
    match n.command:
        case "extract":
            extract_locale()
        case "compile":
            compile_locale()
        case "update":
            update_locale(n.lang)
        case "full_update":
            full_update_locale(n.lang)
        case _:
            return parser.print_help()


if __name__ == "__main__":
    main()
