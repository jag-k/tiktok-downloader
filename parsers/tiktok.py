import logging
import re
from typing import Match

import aiohttp

from parsers.base import Parser as BaseParser, ParserType, Video

logger = logging.getLogger(__name__)


class Parser(BaseParser):
    REG_EXPS = [
        # https://vt.tiktok.com/ZSRq1jcrg/
        re.compile(
            r"(?:https?://)?(?:\w{,2}\.)?tiktok\.com/(?P<id>\w+)/?"
        ),
        # # https://vt.tiktok.com/ZSRq1jcrg/
        # re.compile(
        #     r"(?:https?://)?(?:www.)?tiktok\.com/(?P<id>\w+)/?"
        # )
    ]

    @classmethod
    async def _parse(
            cls,
            session: aiohttp.ClientSession,
            match: Match
    ) -> list[Video]:
        video_id = match.group('id')
        if not video_id:
            return []

        url = f"https://vm.tiktok.com/{video_id}"
        logger.info("Getting video link from: %s", url)
        async with session.get(
                "https://api.douyin.wtf/api",
                params={
                    "url": url
                }
        ) as response:
            data = await response.json()

        logger.debug("Got data: %s", data)

        url = data.get("nwm_video_url", None)
        if url:
            video = Video(
                url=url,
                type=ParserType.TIKTOK,
                caption=data.get("video_title", None),
                thumbnail_url=data.get("video_cover", None),
                author=data.get("video_author_nickname", None),
            )
            if video:
                return [video]
            return []
