from babel.messages.frontend import extract_messages

from app.constants import DOMAIN, LOCALE_PATH
from cli.distributions import dist


def main() -> None:
    obj = extract_messages(dist)
    obj.width = 80
    obj.output_file = LOCALE_PATH / f"{DOMAIN}.pot"
    obj.input_dirs = ["."]
    obj.sort_by_file = True
    obj.keywords = "_n:1,2"
    obj.msgid_bugs_address = dist.get_author_email()
    obj.description = dist.get_description()
    obj.finalize_options()
    obj.run()


if __name__ == "__main__":
    main()
