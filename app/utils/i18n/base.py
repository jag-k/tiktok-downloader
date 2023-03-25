from collections.abc import Iterator
from contextvars import ContextVar
from gettext import NullTranslations, translation
from typing import Union

from app import constants

__all__ = (
    "CURRENT_LANG",
    "ContextGetText",
    "Str",
)

CURRENT_LANG = ContextVar("CURRENT_LANG", default=constants.DEFAULT_LOCALE)

_translations: dict[str, NullTranslations] = {}

Str = Union[str, "ContextGetText"]


class ContextGetText:
    def __init__(self, *args, type_: str = "gettext"):
        self.args = args
        self.type = type_

    def __str__(self):
        lang = CURRENT_LANG.get()
        path = constants.LOCALE_PATH
        t = _translations.get(lang, None)
        if t is None:
            t = translation(
                domain=constants.DOMAIN,
                localedir=path,
                languages=[lang],
                fallback=True,
            )
        func = getattr(t, self.type, None)
        if func is None:
            return str(self.args[0])

        _translations[lang] = t

        return func(*self.args)

    @property
    def s(self):
        return str(self)

    def __repr__(self):
        args = ", ".join(map(repr, self.args))
        return f"{self.__class__.__name__}.{self.type}({args})"

    def __getattr__(self, item):
        return getattr(str(self), item)

    def __len__(self) -> int:
        return len(str(self))

    def __add__(self, __other: str) -> str:
        return str(self).__add__(__other)

    def __mul__(self, __n: int) -> str:
        return str(self).__mul__(__n)

    def __rmul__(self, __n: int) -> str:
        return str(self).__rmul__(__n)

    def __mod__(self, __other) -> str:
        return str(self).__mod__(__other)

    def __contains__(self, __other: str) -> bool:
        return str(self).__contains__(__other)

    def __getitem__(self, __key: int | slice) -> str:
        return str(self).__getitem__(__key)

    def __iter__(self) -> Iterator[str]:
        return str(self).__iter__()

    def __eq__(self, __other: str) -> bool:
        return str(self).__eq__(__other)

    def __ne__(self, __other: str) -> bool:
        return str(self).__ne__(__other)

    def __hash__(self) -> int:
        return str(self).__hash__()

    def __format__(self, __format_spec: str) -> str:
        return str(self).__format__(__format_spec)

    def __sizeof__(self) -> int:
        return str(self).__sizeof__()
