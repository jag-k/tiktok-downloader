# flake8: noqa: E402

import argparse
import inspect
import os

os.putenv("CLI_MODE", "1")

from cli.comands import commands

parser = argparse.ArgumentParser(description="Manage translations")

parser.add_argument(
    "command",
    choices=list(commands.keys()),
    help="Command to run",
)

parser.add_argument("-l", "--lang", default="ru")


def main():
    n = parser.parse_args()
    cmd = commands.get(n.command, None)
    if cmd:
        if inspect.signature(cmd).parameters:
            return cmd(n.lang)
        return cmd()
    return parser.print_help()


if __name__ == "__main__":
    main()
