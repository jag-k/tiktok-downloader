import json
from collections.abc import Iterator
from contextvars import ContextVar
from gettext import NullTranslations, translation
from typing import Any, Union

from telegram import TelegramObject
from telegram.request._requestparameter import RequestParameter

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
    def __init__(self, *args, type_: str = "gettext") -> None:
        self.args = args
        self.type = type_

    def __str__(self) -> str:
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
    def s(self) -> str:
        return str(self)

    def __repr__(self) -> str:
        args = ", ".join(map(repr, self.args))
        return f"{self.__class__.__name__}.{self.type}({args})"

    def __getattr__(self, item) -> None:
        return getattr(str(self), item)

    def __len__(self) -> int:
        return len(str(self))

    def __add__(self, __other: str) -> str:
        return str(self).__add__(__other)

    def __radd__(self, __other: str) -> str:
        return __other.__add__(str(self))

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


# Patch json dumps in python-telegram-bot
def convert(obj: Any | ContextGetText) -> Any | str:
    if isinstance(obj, ContextGetText):
        return obj.s
    return obj


def to_json(self: TelegramObject) -> str:
    """Gives a JSON representation of an object.

    .. versionchanged:: 20.0
        Now includes all entries of :attr:`api_kwargs`.

    Returns:
        :obj:`str`
    """
    return json.dumps(self.to_dict(), default=convert)


TelegramObject.to_json = to_json


@property  # type: ignore[misc]
def json_value(self: RequestParameter) -> str | None:
    """The JSON dumped :attr:`value` or :obj:`None` if :attr:`value` is :obj:`None`.
    The latter can currently only happen if :attr:`input_files` has exactly one element that
    must not be uploaded via an attach:// URI.
    """
    if isinstance(self.value, ContextGetText):
        return self.value.s
    if isinstance(self.value, str):
        return self.value
    if self.value is None:
        return None
    return json.dumps(self.value, default=convert)


# noinspection PyPropertyAccess
RequestParameter.json_value = json_value
