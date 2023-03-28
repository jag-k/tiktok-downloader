from collections.abc import Callable
from typing import Any, TypeVar

from app.constants import Keys
from app.context import CallbackContext
from app.parsers import Media, ParserType
from app.utils.i18n import _

MAKE_CAPTION_DEFAULT = TypeVar("MAKE_CAPTION_DEFAULT", bound=Any)


def make_caption(
    ctx: CallbackContext, default: MAKE_CAPTION_DEFAULT = None
) -> Callable[[Media], str | MAKE_CAPTION_DEFAULT]:
    add_caption = ctx.settings[Keys.DESCRIPTION_FLAG]
    add_autor = ctx.settings[Keys.ADD_AUTHOR_MENTION]
    add_link = ctx.settings[Keys.ADD_ORIGINAL_LINK]
    add_flag = ctx.settings[Keys.TIKTOK_FLAG]

    def caption(media: Media) -> str | MAKE_CAPTION_DEFAULT:
        media_caption = ""
        if add_caption:
            media_caption += media.caption or ""
        if add_autor:
            media_caption += _(" by <code>@{author}</code> ").format(
                author=media.author
            )
        if add_flag:
            media_caption += f" {media.language_emoji}"
        if add_link and media.type != ParserType.TWITTER:
            media_caption += f"\n\n{media.original_url}"
        return media_caption.strip() or default

    return caption
