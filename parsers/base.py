import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from re import Match
from typing import re, Type

import aiohttp
from telegram._utils.enum import StringEnum  # noqa


logger = logging.Logger(__name__)


class ParserType(StringEnum):
    """Parser type."""

    TIKTOK = "TikTok"
    TWITTER = "Twitter"
    YOUTUBE = "YouTube"


@dataclass
class Video:
    url: str
    type: ParserType
    caption: str | None
    thumbnail_url: str | None
    author: str | None


class Parser(ABC):
    REG_EXPS: list[re] = []
    _parsers: list[Type['Parser']] = []

    @classmethod
    @abstractmethod
    async def _parse(
            cls,
            session: aiohttp.ClientSession,
            match: Match
    ) -> list[Video]:
        raise NotImplementedError

    @classmethod
    async def parse(
            cls,
            session: aiohttp.ClientSession,
            *strings: str,
    ) -> list[Video]:
        result: list[Video] = []
        for string in strings:
            for parser in cls._parsers:
                for reg_exp in parser.REG_EXPS:
                    for match in reg_exp.finditer(string):
                        logger.info("Found match for %r: %s", (parser, match))
                        videos = await parser._parse(session, match)
                        result.extend(videos)
        return result

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Parser._parsers.append(cls)
