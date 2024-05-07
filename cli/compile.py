from babel.messages.frontend import compile_catalog
from constants.paths import LOCALE_PATH

from app.constants import DOMAIN
from cli.distributions import dist


def main() -> None:
    obj = compile_catalog(dist)
    obj.domain = DOMAIN
    obj.directory = LOCALE_PATH
    obj.statistics = True
    obj.description = dist.get_description()
    obj.finalize_options()
    obj.run()


if __name__ == "__main__":
    main()
