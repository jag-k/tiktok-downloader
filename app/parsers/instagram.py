import json
import logging
import re
from re import Match

import aiohttp

from app.parsers.base import Media, ParserType, Video
from app.parsers.base import Parser as BaseParser

logger = logging.getLogger(__name__)

INSTAGRAM_RE = re.compile(
    r"(?:https?://)?(?:www\.)?instagram\.com/(?P<type>\w+)/(?P<id>\w+)"
)


class Parser(BaseParser):
    TYPE = ParserType.INSTAGRAM
    REG_EXPS = [
        # https://www.instagram.com/p/CTQZ5Y8J8ZU/
        # https://www.instagram.com/reel/CTQZ5Y8J8ZU/
        INSTAGRAM_RE,
    ]
    CUSTOM_EMOJI_ID = 5465453979896913711  # 💬

    @classmethod
    def _is_supported(cls) -> bool:
        return True

    @classmethod
    async def _parse(
        cls, session: aiohttp.ClientSession, match: Match
    ) -> list[Media]:
        post_id = match.group("id")
        post_type = match.group("type")

        original_url = f"https://www.instagram.com/{post_type}/{post_id}"

        logger.info("Getting video link from: %s", original_url)

        async with session.get(
            "https://www.instagram.com/graphql/query/",
            params={
                "query_hash": "b3055c01b4b222b8a47dc12b090e4e64",
                "variables": json.dumps({"shortcode": post_id}),
            },
        ) as response:
            data: dict = await response.json()
        logger.debug("Got data: %s", data)
        shortcode_media = data.get("data", {}).get("shortcode_media", {})

        if not shortcode_media.get("is_video", False):
            logger.info("%s is not a video", original_url)
            return []
        caption = shortcode_media.get("title", None)
        if not caption:
            caption = " ".join(
                [
                    node.get("node", {}).get("text", "")
                    for node in shortcode_media.get(
                        "edge_media_to_caption", {}
                    ).get("edges", [])
                ]
            ).strip()

        return [
            Video(
                caption=caption or None,
                type=cls.TYPE,
                original_url=original_url,
                thumbnail_url=shortcode_media.get("display_url", None),
                author=shortcode_media.get("owner", {}).get("username", None),
                url=shortcode_media.get("video_url", ""),
            )
        ]
