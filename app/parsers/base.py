import logging
import time
from abc import ABC, abstractmethod
from re import Match, Pattern
from typing import ClassVar, final

import aiohttp

from app.database import MediaCache as MediaCacheDB
from app.models.medias import Media, ParserType

logger = logging.getLogger(__name__)

__all__ = (
    "Parser",
    "MediaCache",
)


class MediaCache:
    class FoundCache(Exception):
        def __init__(self, medias: list[Media], original_url: str, *args) -> None:
            super().__init__(medias, original_url, *args)
            self.medias = medias
            self.original_url = original_url

    @classmethod
    async def find_by_original_url(cls, original_url: str | None = None) -> None:
        data = await MediaCacheDB.get_medias(original_url)
        if data:
            raise cls.FoundCache(
                medias=data,
                original_url=original_url,
            )

    @staticmethod
    async def save(media: Media) -> Media:
        res = await MediaCacheDB.save_medias(media)
        logger.info("Saved item to cache for %s", res)
        return media

    @classmethod
    async def save_group(cls, medias: list[Media]) -> list[Media]:
        res = await MediaCacheDB.save_medias(*medias)
        logger.info("Saved %d item(s) to cache for %s", len(medias), res)
        return medias


class Parser(ABC):
    TYPE: ClassVar[ParserType | None] = None
    REG_EXPS: ClassVar[list[Pattern]] = []
    _parsers: ClassVar[list[type["Parser"]]] = []
    CUSTOM_EMOJI_ID: ClassVar[int] = 0

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
        cache: MediaCache,
    ) -> list[Media]:
        raise NotImplementedError

    @classmethod
    @final
    async def parse(
        cls,
        session: aiohttp.ClientSession,
        *strings: str,
    ) -> list[Media]:
        result: list[Media] = []
        start_time = time.time()
        for string in strings:
            for parser in cls._parsers:
                for reg_exp in parser.REG_EXPS:
                    match = reg_exp.match(string)
                    if not match:
                        continue
                    logger.info("Found match for %s: %r", parser.TYPE, match.string)
                    try:
                        medias = await parser._parse(session, match, cache=MediaCache())
                    except MediaCache.FoundCache as e:
                        medias = e.medias
                        logger.info("Found cache for %s", e.original_url)
                    result.extend(medias)
                    break
        logger.info(
            "Parsed %d items in %.4f seconds",
            len(result),
            time.time() - start_time,
        )
        return result

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls._is_supported():
            logger.info("Registering Parser[%s]", cls.TYPE)
            Parser._parsers.append(cls)
