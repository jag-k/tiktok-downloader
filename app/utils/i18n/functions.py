from app.utils.i18n.base import ContextGetText

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


def gettext(message: str) -> ContextGetText:
    return ContextGetText(message, type_="gettext")


def ngettext(msgid1: str, msgid2: str, n: int) -> ContextGetText:
    return ContextGetText(msgid1, msgid2, n, type_="ngettext")


def pgettext(context: str, message: str) -> ContextGetText:
    return ContextGetText(context, message, type_="pgettext")


def npgettext(context: str, msgid1: str, msgid2: str, n: int) -> ContextGetText:
    return ContextGetText(context, msgid1, msgid2, n, type_="npgettext")


def _(message: str) -> ContextGetText:
    return gettext(message)


def _n(msgid1: str, msgid2: str, n: int) -> ContextGetText:
    return ngettext(msgid1, msgid2, n)


def _p(context: str, message: str) -> ContextGetText:
    return pgettext(context, message)


def _np(context: str, msgid1: str, msgid2: str, n: int) -> ContextGetText:
    return npgettext(context, msgid1, msgid2, n)
