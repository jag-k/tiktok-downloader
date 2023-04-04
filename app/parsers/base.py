import functools
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from re import Match, Pattern
from string import ascii_uppercase
from typing import Any, TypeVar

import aiohttp
import telegram
from aiohttp import ClientSession
from telegram import InputFile, InputMediaVideo
from telegram._utils.enum import StringEnum  # noqa

from app.constants import Keys
from app.context import CallbackContext

# noinspection PyProtectedMember
from app.utils.i18n import _

logger = logging.getLogger(__name__)

FLAG_OFFSET = ord("🇦") - ord("A")


@functools.lru_cache
def lang_emoji(lang: str) -> str:
    if isinstance(lang, str) and len(lang) == 2:
        lang = lang.upper()
        if all(x in ascii_uppercase for x in lang):
            return "".join(chr(ord(c) + FLAG_OFFSET) for c in lang)
    return ""


class ParserType(StringEnum):
    """Parser type."""

    TIKTOK = "TikTok"
    TWITTER = "Twitter"
    YOUTUBE = "YouTube"
    REDDIT = "Reddit"
    INSTAGRAM = "Instagram"


@dataclass(kw_only=True)
class Media:
    caption: str
    type: ParserType
    original_url: str
    caption: str | None = None
    thumbnail_url: str | None = None
    author: str | None = None
    extra_description: str = ""
    language: str | None = None

    def __post_init__(self):
        self.language_emoji = self.language

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

    MAKE_CAPTION_DEFAULT = TypeVar("MAKE_CAPTION_DEFAULT", bound=Any)

    def real_caption(
        self, ctx: CallbackContext, default: MAKE_CAPTION_DEFAULT = None
    ) -> str | MAKE_CAPTION_DEFAULT:
        add_caption = ctx.settings[Keys.DESCRIPTION_FLAG]
        add_autor = ctx.settings[Keys.ADD_AUTHOR_MENTION]
        add_link = ctx.settings[Keys.ADD_ORIGINAL_LINK]
        add_flag = ctx.settings[Keys.TIKTOK_FLAG]

        media_caption = ""
        if add_caption:
            media_caption += self.caption or ""
        if add_autor:
            media_caption += _(" by <code>@{author}</code> ").format(
                author=self.author
            )
        if add_flag:
            media_caption += f" {self.language_emoji}"
        if add_link and self.type != ParserType.TWITTER:
            media_caption += f"\n\n{self.original_url}"
        return media_caption.strip() or default

    async def update(
        self,
        update: telegram.Update,
        ctx: CallbackContext,
        message: telegram.Message | None = None,
    ):
        _ = update, ctx
        return message


@dataclass(kw_only=True)
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

    async def update(
        self,
        update: telegram.Update,
        ctx: CallbackContext,
        message: telegram.Message | None = None,
    ):
        _ = update
        if message:
            await self.content()
            ctx.media_cache[self.original_url] = self
            res = await message.edit_media(
                media=self.file_media(ctx),
            )
            ctx.tg_video_cache[self.original_url] = res.video
            return res

    def __repr__(self):
        return (
            f"Video(url={self.url}, max_quality_url={self.max_quality_url}, "
            f"audio_url={self.audio_url}, mime_type={self.mime_type})"
        )


@dataclass(kw_only=True)
class MediaGroup(Media):
    input_medias: list[
        telegram.InputMediaAudio
        | telegram.InputMediaDocument
        | telegram.InputMediaPhoto
        | telegram.InputMediaVideo
    ] = field(default_factory=list)


@dataclass(kw_only=True)
class Images(Media):
    images: list[str] = field(default_factory=list)
    audio_url: str | None = None


@dataclass(kw_only=True)
class Audio(Media):
    url: str = ""
    mime_type: str = "video/mp4"


class Parser(ABC):
    TYPE: ParserType | None = None
    REG_EXPS: list[Pattern] = []
    _parsers: list[type["Parser"]] = []
    CUSTOM_EMOJI_ID: int = 0

    @classmethod
    @abstractmethod
    def _is_supported(cls) -> bool:
        raise NotImplementedError

    @classmethod
    def parsers(cls) -> list[type["Parser"]]:
        return Parser._parsers

    @classmethod
    @abstractmethod
    async def _parse(
        cls,
        session: aiohttp.ClientSession,
        match: Match,
        cache: dict[str, Media] | None = None,
    ) -> list[Media]:
        raise NotImplementedError

    @classmethod
    async def parse(
        cls,
        session: aiohttp.ClientSession,
        *strings: str,
        cache: dict[str, Media] | None = None,
    ) -> list[Media]:
        result: list[Media] = []
        for string in strings:
            for parser in cls._parsers:
                for reg_exp in parser.REG_EXPS:
                    match = reg_exp.fullmatch(string)
                    if not match:
                        continue
                    logger.info(
                        "Found match for %s: %r", parser.TYPE, match.string
                    )
                    medias = await parser._parse(session, match, cache=cache)
                    result.extend(medias)
                    break
        return result

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._is_supported():
            logger.info("Registering Parser[%s]", cls.TYPE)
            Parser._parsers.append(cls)
