import functools
import re
from string import ascii_uppercase
from typing import Any, TypeVar

import telegram
from aiohttp import ClientSession
from pydantic import Field
from telegram import InputFile, InputMediaVideo

# noinspection PyProtectedMember
from telegram._utils.enum import StringEnum

from app.constants import Keys
from app.context import CallbackContext
from app.models.base import Model
from app.settings.user_settings import DescriptionTypes

# noinspection PyProtectedMember
from app.utils.i18n import _

MAKE_CAPTION_DEFAULT = TypeVar("MAKE_CAPTION_DEFAULT", bound=Any)
FLAG_OFFSET = ord("🇦") - ord("A")


class ParserType(StringEnum):
    """Parser type."""

    TIKTOK = "TikTok"
    TWITTER = "Twitter"
    YOUTUBE = "YouTube"
    REDDIT = "Reddit"
    INSTAGRAM = "Instagram"


@functools.lru_cache
def lang_emoji(lang: str) -> str:
    if isinstance(lang, str) and len(lang) == 2:
        lang = lang.upper()
        if all(x in ascii_uppercase for x in lang):
            return "".join(chr(ord(c) + FLAG_OFFSET) for c in lang)
    return ""


class Media(Model):
    caption: str
    type: ParserType
    original_url: str
    caption: str | None = None
    thumbnail_url: str | None = None
    author: str | None = None
    extra_description: str = ""
    language: str | None = None

    @property
    def language_emoji(self) -> str:
        return lang_emoji(self.language.upper()) if self.language else ""

    @language_emoji.setter
    def language_emoji(self, value: str):
        if (
            isinstance(value, str)
            and len(value) == 2
            and all(x in ascii_uppercase for x in value)
        ):
            self.language = value.upper()
        else:
            self.language = None

    def __hash__(self):
        return hash(self.original_url)

    def real_caption(
        self, ctx: CallbackContext, default: MAKE_CAPTION_DEFAULT = None
    ) -> str | MAKE_CAPTION_DEFAULT:
        add_caption = ctx.settings[Keys.ADD_DESCRIPTION]
        add_autor = ctx.settings[Keys.ADD_AUTHOR_MENTION]
        add_link = ctx.settings[Keys.ADD_ORIGINAL_LINK]
        add_flag = ctx.settings[Keys.TIKTOK_FLAG]

        media_caption = ""
        match add_caption:
            case DescriptionTypes.FULL:
                media_caption += self.caption or ""
            case DescriptionTypes.WITHOUT_HASHTAGS:
                media_caption += re.sub(r"#\w+\s?", "", self.caption or "")

        media_caption = media_caption.strip()

        if add_autor:
            media_caption += _(" by <code>@{author}</code> ").format(
                author=self.author
            )
        media_caption = media_caption.strip()

        if add_flag:
            media_caption += f" {self.language_emoji}"
        media_caption = media_caption.strip()

        if add_link and self.type != ParserType.TWITTER:
            media_caption += f"\n\n{self.original_url}"
        return media_caption.strip() or default


class Video(Media):
    url: str = ""
    max_quality_url: str | None = None
    audio_url: str | None = None
    mime_type: str = "video/mp4"
    video_content: bytes | None = None
    video_height: int | None = None
    video_width: int | None = None
    video_duration: int | None = None

    def __bool__(self):
        return bool(self.url)

    async def content(
        self,
        user_agent: str | None = None,
    ) -> bytes:
        if self.video_content:
            return self.video_content

        headers = {}
        if user_agent is not None:
            headers["User-Agent"] = user_agent

        async with ClientSession(headers=headers) as session:
            async with session.get(self.url) as resp:
                self.video_content = await resp.content.read()
        return self.video_content

    @property
    def file_input(self) -> InputFile | None:
        if not self.video_content:
            return None
        return InputFile(self.video_content, filename=self.original_url)

    def file_media(self, ctx: CallbackContext) -> InputMediaVideo | None:
        if not self.video_content:
            return None
        return InputMediaVideo(
            self.file_input,
            caption=self.real_caption(ctx),
            width=self.video_width,
            height=self.video_height,
            duration=self.video_duration,
            supports_streaming=True,
            filename=self.original_url,
            thumbnail=self.thumbnail_url,
        )


class MediaGroup(Media):
    input_medias: list[
        telegram.InputMediaAudio
        | telegram.InputMediaDocument
        | telegram.InputMediaPhoto
        | telegram.InputMediaVideo
    ] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class Images(Media):
    images: list[str] = Field(default_factory=list)
    audio_url: str | None = None


class Audio(Media):
    url: str = ""
    mime_type: str = "audio/mpeg"


if __name__ == "__main__":
    m = Video(
        type=ParserType.YOUTUBE,
        original_url="https://www.youtube.com/watch?v=QH2-TGUlwu4",
        url="https://www.youtube.com/watch?v=QH2-TGUlwu4",
    )
    print(repr(m))
    print(repr(m.type))
    d = m.to_dict()
    print(d)
    m2 = Media.from_dict(d)
    print(repr(m))
    print(repr(m2.type))
