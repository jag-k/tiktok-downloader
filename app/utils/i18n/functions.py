from app.utils.i18n.base import ContextGetText, Str

__all__ = (
    "gettext",
    "ngettext",
    "pgettext",
    "npgettext",
    "_",
    "_n",
    "_p",
    "_np",
)


def gettext(message: str) -> Str:
    return ContextGetText(message, type_="gettext")


def ngettext(msgid1: str, msgid2: str, n: int) -> Str:
    return ContextGetText(msgid1, msgid2, n, type_="ngettext")


def pgettext(context: str, message: str) -> Str:
    return ContextGetText(context, message, type_="pgettext")


def npgettext(context: str, msgid1: str, msgid2: str, n: int) -> Str:
    return ContextGetText(context, msgid1, msgid2, n, type_="npgettext")


def _(message: str) -> Str:
    return gettext(message)


def _n(msgid1: str, msgid2: str, n: int) -> Str:
    return ngettext(msgid1, msgid2, n)


def _p(context: str, message: str) -> Str:
    return pgettext(context, message)


def _np(context: str, msgid1: str, msgid2: str, n: int) -> Str:
    return npgettext(context, msgid1, msgid2, n)
