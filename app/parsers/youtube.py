import logging
import re
from re import Match

import aiohttp
import pytube as pytube
from pytube import StreamQuery
from pytube.exceptions import PytubeError

from app import constants
from app.parsers.base import Media, ParserType, Video
from app.parsers.base import Parser as BaseParser
from app.utils.time_it import timeit

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
            r")(?P<id>[\w-]+)"
        ),
        # https://youtube.com/shorts/hBOLCcvbGHM
        # https://youtube.com/watch?v=hBOLCcvbGHM
        re.compile(
            r"(?:https?://)?(?:www\.)?youtube\.com/shorts/(?P<id>[\w-]+)"
        ),
    ]
    CUSTOM_EMOJI_ID = 5463206079913533096  # 📹

    @classmethod
    def _is_supported(cls) -> bool:
        return True

    @classmethod
    async def _parse(
        cls, session: aiohttp.ClientSession, match: Match
    ) -> list[Media]:
        try:
            yt_id = match.group("id")
        except IndexError:
            return []

        original_url = f"https://youtube.com/watch?v={yt_id}"

        logger.info("Getting video link from: %s", original_url)
        yt = pytube.YouTube(original_url)
        with timeit("Getting streams", logger):
            streams_obj = StreamQuery(yt.fmt_streams)

        streams = streams_obj.filter(
            type="video", progressive=True, file_extension="mp4"
        ).order_by("resolution")
        logger.info("Found %s streams", len(streams))
        stream = streams.last()
        if not stream:
            logger.info("No suitable streams found")
            return []

        max_quality_url = stream.url
        max_fs = 0

        for st in streams:
            logger.info("Stream: %s", st)
            file_size = st.filesize
            logger.info("Stream file size: %s", file_size)
            if constants.TG_FILE_LIMIT >= file_size > max_fs:
                logger.info("Found suitable stream with filesize %s", file_size)
                max_fs = file_size
                stream = st

        logger.info("Selected stream: %s", stream)

        try:
            video = Video(
                author=yt.author,
                caption=yt.title,
                thumbnail_url=yt.thumbnail_url,
                type=ParserType.YOUTUBE,
                url=stream.url,
                original_url=original_url,
                max_quality_url=max_quality_url,
                mime_type=stream.mime_type,
            )
        except PytubeError as err:
            logger.error(
                "Failed to get video %r with error: %s", original_url, err
            )
            return []
        return [video]
