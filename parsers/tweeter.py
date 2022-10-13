import logging
import os
import re
from typing import Match

import aiohttp

from parsers.base import Parser as BaseParser, ParserType, Video

logger = logging.getLogger(__name__)

TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")


class Parser(BaseParser):
    REG_EXPS = [
        re.compile(
            r"(?:https?://)?"
            r"(?:www\.)?"
            r"twitter\.com/"
            r"(?P<user>\w+)/status/(?P<id>\d+)"
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
        tweet_id = match.group('id')
        if not tweet_id:
            return []

        logger.info(
            "Getting video link from: https://twitter.com/i/status/%s",
            tweet_id
        )

        async with session.get(
                f"https://api.twitter.com/2/tweets/{tweet_id}",
                params={
                    "media.fields": ','.join((
                            "type",
                            "variants",
                    )),
                    "expansions": ','.join((
                            "attachments.media_keys",
                            "author_id",
                    )),
                    "user.fields": ','.join((
                            "username",
                    )),
                },
                headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
        ) as response:
            data: dict = await response.json()

        logger.debug("Got data: %s", data)
        includes = data.get("includes", {})
        medias = includes.get("media", [])
        author = includes.get("users", [{}])[0].get("username", None)
        caption = data.get("data", {}).get("text", None)

        result = []
        for media in medias:
            if media.get('type') == 'video':
                thumbnail_url = media.get('preview_image_url')
                result.append(
                    Video(
                        url=max(
                            media.get('variants', []),
                            key=lambda x: x.get("bit_rate", 0)
                        ).get("url"),
                        caption=caption,
                        thumbnail_url=thumbnail_url,
                        type=ParserType.TWITTER,
                        author=author,
                    )
                )
        return result
