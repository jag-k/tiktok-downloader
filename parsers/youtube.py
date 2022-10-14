import logging
import re
from typing import Match

import aiohttp
import pytube as pytube
from pytube.exceptions import VideoUnavailable, PytubeError

from parsers.base import Parser as BaseParser, ParserType, Video

logger = logging.getLogger(__name__)


class Parser(BaseParser):
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

    @classmethod
    async def _parse(
            cls,
            session: aiohttp.ClientSession,
            match: Match
    ) -> list[Video]:
        try:
            yt_id = match.group('id')
        except IndexError:
            return []

        url = f"https://youtu.be/{yt_id}"

        logger.info("Getting video link from: %s", url)
        yt = pytube.YouTube(url)

        try:
            # FIXME: This solution is extremely slow + it's synchronous
            video = Video(
                author=yt.author,
                caption=yt.title,
                thumbnail_url=yt.thumbnail_url,
                type=ParserType.YOUTUBE,
                url=yt.streams.get_highest_resolution().url,
            )
        except PytubeError:
            return []
        return [video]
