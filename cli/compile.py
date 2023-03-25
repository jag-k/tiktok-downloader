from babel.messages.frontend import compile_catalog

from app.constants import DOMAIN, LOCALE_PATH
from cli.distributions import dist


def main():
    obj = compile_catalog(dist)
    obj.domain = DOMAIN
    obj.directory = LOCALE_PATH
    obj.statistics = True
    obj.description = dist.get_description()
    obj.finalize_options()
    obj.run()


if __name__ == "__main__":
    main()
