from babel.messages.frontend import extract_messages

from app.constants import LOCALE_PATH, DOMAIN
from cli.distributions import dist


def main():
    obj = extract_messages(dist)
    obj.width = 80
    obj.output_file = LOCALE_PATH / f'{DOMAIN}.pot'
    obj.input_dirs = ['app']
    obj.sort_by_file = True
    obj.msgid_bugs_address = dist.get_author_email()
    obj.description = dist.get_description()
    obj.finalize_options()
    obj.run()


if __name__ == '__main__':
    main()
