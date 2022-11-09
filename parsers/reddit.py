import logging
import os
import re
from typing import Match
from urllib.parse import urlparse

import aiohttp
from aiohttp import InvalidURL

from parsers.base import Parser as BaseParser, ParserType, Video, Media

logger = logging.getLogger(__name__)

USER_AGENT = os.getenv("REDDIT_USER_AGENT", "video downloader (by u/Jag_k)")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

AUTH = aiohttp.BasicAuth(
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
)


def id_from_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.netloc:
        raise InvalidURL(url)
    parts = parsed.path.rstrip("/").split("/")

    if "comments" not in parts and "gallery" not in parts:
        submission_id = parts[-1]
        if "r" in parts:
            # Invalid URL (subreddit, not submission)
            raise InvalidURL(url)

    elif "gallery" in parts:
        submission_id = parts[parts.index("gallery") + 1]

    elif parts[-1] == "comments":
        # Invalid URL (submission ID not present)
        raise InvalidURL(url)

    else:
        submission_id = parts[parts.index("comments") + 1]

    if not submission_id.isalnum():
        raise InvalidURL(url)
    return submission_id


async def comment(session: aiohttp.ClientSession, comment_id: str) -> dict:
    async with session.get(
            f"https://api.reddit.com/comments/{comment_id}",
            auth=AUTH,
            headers={"User-Agent": USER_AGENT}
    ) as resp:
        data = await resp.json()
    return data[0].get("data", {}).get("children", [{}])[0].get("data", {})


class Parser(BaseParser):
    REG_EXPS = [
        # redd.it/2gmzqe
        re.compile(
            r"(?:https?://)?(?:www\.)?redd\.it/(?P<id>\w+)"
        ),
        # reddit.com/comments/2gmzqe/
        # www.reddit.com/r/redditdev/comments/2gmzqe/praw_https/
        # www.reddit.com/gallery/2gmzqe
        re.compile(
            r"(?:https?://)?(?:www\.)?reddit\.com/(?P<link>[\w/]+)"
        )
    ]
    CUSTOM_EMOJI_ID = 5465648490375814741  # 💬

    @classmethod
    def _is_supported(cls) -> bool:
        return bool(USER_AGENT and REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)

    @classmethod
    async def _parse(
            cls,
            session: aiohttp.ClientSession,
            match: Match
    ) -> list[Media]:
        try:
            comment_id = match.group('id')
        except (IndexError, InvalidURL):
            try:
                comment_id = id_from_url(
                    f"https://reddit.com/{match.group('link')}"
                )
            except (IndexError, InvalidURL):
                return []

        original_url = f"https://redd.it/{comment_id}"

        logger.info("Getting video link from: %s", original_url)
        cmt = await comment(session, comment_id)
        media = cmt.get("media", {}).get("reddit_video", {})
        if not media:
            return []

        video_url = media.get("fallback_url", '').rstrip('?source=fallback')
        if not video_url:
            return []

        author = cmt.get("author")
        title = cmt.get("title")
        subreddit = cmt.get("subreddit")

        thumbnail = cmt.get("thumbnail")
        if cmt.get('preview', {}).get('enabled', False):
            thumbnail = cmt["preview"]["images"][0]["source"]["url"]

        # TODO: Get video with audio
        return [
            Video(
                original_url=original_url,
                author=author,
                caption=title,
                thumbnail_url=thumbnail,
                type=ParserType.REDDIT,
                extra_description=f"by u/{author} in r/{subreddit}",
                url=video_url,
            )
        ]
