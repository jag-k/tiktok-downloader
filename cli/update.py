from babel.messages.frontend import update_catalog
from constants.paths import LOCALE_PATH

from app.constants import DEFAULT_LOCALE, DOMAIN
from cli.distributions import dist


def main(lang: str = DEFAULT_LOCALE) -> None:
    obj = update_catalog(dist)
    obj.width = 80
    obj.domain = DOMAIN
    obj.locale = lang
    obj.output_dir = LOCALE_PATH
    obj.input_file = LOCALE_PATH / f"{DOMAIN}.pot"
    obj.previous = True
    obj.update_header_comment = True
    obj.no_fuzzy_matching = True
    obj.msgid_bugs_address = dist.get_author_email()
    obj.description = dist.get_description()
    obj.finalize_options()
    obj.run()


if __name__ == "__main__":
    main()
