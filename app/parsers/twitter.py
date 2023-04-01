import logging
import os
import re
from re import Match

import aiohttp

from app.parsers.base import Media, ParserType, Video
from app.parsers.base import Parser as BaseParser

logger = logging.getLogger(__name__)

TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# https://twitter.com/Yoda4ever/status/1580609309217628160
TWITTER_RE = re.compile(
    r"(?:https?://)?(?:www\.)?twitter\.com/(?P<user>\w+)/status/(?P<id>\d+)"
)


class Parser(BaseParser):
    TYPE = ParserType.TWITTER
    REG_EXPS = [
        TWITTER_RE,
        # https://t.co/sOHvySZwUo
        re.compile(r"(?:https?://)?t\.co/(?P<tco_id>\w+)"),
    ]
    CUSTOM_EMOJI_ID = 5465453979896913711  # 💬

    @classmethod
    def _is_supported(cls) -> bool:
        return bool(TWITTER_BEARER_TOKEN)

    @classmethod
    async def _parse(
        cls,
        session: aiohttp.ClientSession,
        match: Match,
        cache: dict[str, Media] | None = None,
    ) -> list[Media]:
        try:
            tweet_id = match.group("id")
        except IndexError:
            try:
                tco_id = match.group("tco_id")
            except IndexError:
                return []
            async with session.get(f"https://t.co/{tco_id}") as response:
                new_match = TWITTER_RE.match(str(response.real_url))
            return await cls._parse(session, new_match)

        original_url = f"https://twitter.com/i/status/{tweet_id}"

        logger.info("Getting video link from: %s", original_url)

        async with session.get(
            f"https://api.twitter.com/2/tweets/{tweet_id}",
            params={
                "media.fields": ",".join(
                    (
                        "type",
                        "variants",
                    )
                ),
                "expansions": ",".join(
                    (
                        "attachments.media_keys",
                        "author_id",
                    )
                ),
                "user.fields": ",".join(("username",)),
            },
            headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
        ) as response:
            data: dict = await response.json()

        logger.debug("Got data: %s", data)
        includes = data.get("includes", {})
        medias = includes.get("media", [])
        author = includes.get("users", [{}])[0].get("username", None)
        caption = data.get("data", {}).get("text", None)

        result = []
        for media in medias:
            if media.get("type") == "video":
                thumbnail_url = media.get("preview_image_url")
                result.append(
                    Video(
                        url=max(
                            media.get("variants", []),
                            key=lambda x: x.get("bit_rate", 0),
                        ).get("url"),
                        caption=caption,
                        thumbnail_url=thumbnail_url,
                        type=ParserType.TWITTER,
                        author=author,
                        original_url=original_url,
                    )
                )
        return result
