import logging
import re
from typing import Match

import aiohttp
import pytube as pytube
from pytube.exceptions import PytubeError

from app.parsers.base import Parser as BaseParser, ParserType, Video, Media

logger = logging.getLogger(__name__)


class Parser(BaseParser):
    TYPE = ParserType.YOUTUBE
    REG_EXPS = [
        # https://www.youtube.com/watch?v=TCrP1SE2DkY
        # https://youtu.be/TCrP1SE2DkY
        re.compile(
            r"(?:https?://)?"
            r"(?:"
            r"(?:www\.)?youtube\.com/watch\?v="
            r"|youtu.be/"
            r")(?P<id>\w+)"
        ),
        # https://youtube.com/shorts/hBOLCcvbGHM
        # https://youtube.com/watch?v=hBOLCcvbGHM
        re.compile(
            r"(?:https?://)?(?:www\.)?youtube\.com/shorts/(?P<id>\w+)"
        )
    ]
    CUSTOM_EMOJI_ID = 5463206079913533096  # 📹

    @classmethod
    def _is_supported(cls) -> bool:
        return True

    @classmethod
    async def _parse(
            cls,
            session: aiohttp.ClientSession,
            match: Match
    ) -> list[Media]:
        try:
            yt_id = match.group('id')
        except IndexError:
            return []

        original_url = f"https://youtube.com/watch?v={yt_id}"

        logger.info("Getting video link from: %s", original_url)
        yt = pytube.YouTube(original_url)

        try:
            # FIXME: This solution is extremely slow + it's synchronous
            video = Video(
                author=yt.author,
                caption=yt.title,
                thumbnail_url=yt.thumbnail_url,
                type=ParserType.YOUTUBE,
                url=yt.streams.get_highest_resolution().url,
                original_url=original_url,
            )
        except PytubeError as err:
            logger.error(
                "Failed to get video %r with error: %s",
                original_url,
                err
            )
            return []
        return [video]
