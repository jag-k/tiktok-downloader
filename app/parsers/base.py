import functools
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from re import Match
from string import ascii_uppercase
from typing import re, Type, Awaitable, Callable

import aiohttp
import telegram
from telegram._utils.enum import StringEnum  # noqa
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

FLAG_OFFSET = ord("🇦") - ord("A")


@functools.lru_cache()
def lang_emoji(lang: str) -> str:
    if isinstance(lang, str) and len(lang) == 2:
        lang = lang.upper()
        if all(map(lambda x: x in ascii_uppercase, lang)):
            return "".join(chr(ord(c) + FLAG_OFFSET) for c in lang)
    return ''


class ParserType(StringEnum):
    """Parser type."""

    TIKTOK = "TikTok"
    TWITTER = "Twitter"
    YOUTUBE = "YouTube"
    REDDIT = "Reddit"


@dataclass(kw_only=True)
class Media:
    caption: str
    type: ParserType
    original_url: str
    caption: str | None = None
    thumbnail_url: str | None = None
    author: str | None = None
    extra_description: str = ''
    language: str | None = None
    update: Callable[
                [
                    telegram.Update,
                    telegram.Message,
                    telegram.ext.ContextTypes.DEFAULT_TYPE,
                ],
                Awaitable
            ] | None = None

    def __post_init__(self):
        self.language_emoji = self.language

    @property
    def language_emoji(self) -> str:
        return lang_emoji(self.language.upper()) if self.language else ''

    @language_emoji.setter
    def language_emoji(self, value: str):
        if (
                isinstance(value, str)
                and len(value) == 2
                and all(map(lambda x: x in ascii_uppercase, value))
        ):
            self.language = value.upper()
        else:
            self.language = None

    def __hash__(self):
        return hash(self.original_url)


@dataclass(kw_only=True)
class Video(Media):
    url: str = ''
    max_quality_url: str | None = None
    audio_url: str | None = None
    mime_type: str = "video/mp4"

    def __bool__(self):
        return bool(self.url)


@dataclass(kw_only=True)
class MediaGroup(Media):
    input_medias: list[
        telegram.InputMediaAudio |
        telegram.InputMediaDocument |
        telegram.InputMediaPhoto |
        telegram.InputMediaVideo
        ] = field(default_factory=list)


@dataclass(kw_only=True)
class Images(Media):
    images: list[str] = field(default_factory=list)
    audio_url: str | None = None


@dataclass(kw_only=True)
class Audio(Media):
    url: str = ''
    mime_type: str = "video/mp4"


class Parser(ABC):
    TYPE: ParserType | None = None
    REG_EXPS: list[re] = []
    _parsers: list[Type['Parser']] = []
    CUSTOM_EMOJI_ID: int = 0

    @classmethod
    @abstractmethod
    def _is_supported(cls) -> bool:
        raise NotImplementedError

    @classmethod
    def parsers(cls) -> list[Type['Parser']]:
        return Parser._parsers

    @classmethod
    @abstractmethod
    async def _parse(
            cls,
            session: aiohttp.ClientSession,
            match: Match
    ) -> list[Media]:
        raise NotImplementedError

    @classmethod
    async def parse(
            cls,
            session: aiohttp.ClientSession,
            *strings: str,
    ) -> list[Media]:
        result: list[Media] = []
        for string in strings:
            for parser in cls._parsers:
                for reg_exp in parser.REG_EXPS:
                    for match in reg_exp.finditer(string):
                        logger.info("Found match for %r: %s", parser, match)
                        medias = await parser._parse(session, match)
                        result.extend(medias)
        return result

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._is_supported():
            logger.info("Registering Parser[%s]", cls.TYPE)
            Parser._parsers.append(cls)
