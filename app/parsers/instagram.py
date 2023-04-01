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

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/91.0.4472.114 Safari/537.36"
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
        cls,
        session: aiohttp.ClientSession,
        match: Match,
        cache: dict[str, Media] | None = None,
    ) -> list[Media]:
        post_id = match.group("id")
        post_type = match.group("type")

        original_url = f"https://www.instagram.com/{post_type}/{post_id}"

        if cache and (v := cache.get(original_url)):
            return [v]

        logger.info("Getting video link from: %s", original_url)

        variables = {
            "shortcode": post_id,
            "child_comment_count": 3,
            "fetch_comment_count": 40,
            "parent_comment_count": 24,
            "has_threaded_comments": False,
        }
        async with session.get(
            "https://www.instagram.com/graphql/query/",
            params={
                "query_hash": "477b65a610463740ccdb83135b2014db",
                "variables": json.dumps(variables, separators=(",", ":")),
            },
        ) as response:
            data: dict = await response.json()
        logger.info("Got data: %s", data)
        shortcode_media = data.get("data", {}).get("shortcode_media") or {}

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
        url = shortcode_media.get("video_url", None)
        if not url:
            return []

        thumbnail_url = shortcode_media.get("display_url", None)

        video = Video(
            caption=caption or None,
            type=cls.TYPE,
            original_url=original_url,
            thumbnail_url=thumbnail_url,
            author=shortcode_media.get("owner", {}).get("username", None),
            url=url,
            mime_type="video/mp4",
            video_width=shortcode_media.get("dimensions", {}).get(
                "width", None
            ),
            video_height=shortcode_media.get("dimensions", {}).get(
                "height", None
            ),
            video_duration=int(shortcode_media.get("video_duration", "0"))
            or None,
        )
        if cache is not None:
            cache[video.original_url] = video
        return [video]


if __name__ == "__main__":
    import asyncio

    async def main():
        async with aiohttp.ClientSession() as session:
            print(
                await Parser.parse(
                    session,
                    "https://www.instagram.com/reel/CqYq8vroPH2",
                )
            )

    asyncio.run(main())
