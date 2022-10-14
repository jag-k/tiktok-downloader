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
            r"(?:https?://)?(?:vm\.)?tiktok\.com/(?P<id>\w+)/?"
        ),

        # https://www.tiktok.com/@thejoyegg/video/7136001098841591041
        re.compile(
            r"(?:https?://)?"
            r"(?:www.)?tiktok\.com/@(?P<author>\w+)/video/(?P<video_id>\d+)/?"
        )
    ]

    @classmethod
    async def _parse(
            cls,
            session: aiohttp.ClientSession,
            match: Match
    ) -> list[Video]:
        try:
            video_id = match.group('id')
            url = f"https://vm.tiktok.com/{video_id}"
        except IndexError:
            author = match.group('author')
            video_id = match.group('video_id')
            url = f"https://www.tiktok.com/@{author}/video/{video_id}"

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
