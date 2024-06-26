import asyncio
import json
import logging
import re
from re import Match

import aiohttp

from app.constants import CONFIG_PATH, LAMADAVA_SAAS_TOKEN
from app.models.medias import Media, ParserType, Video

from .base import MediaCache
from .base import Parser as BaseParser

logger = logging.getLogger(__name__)

INSTAGRAM_RE = re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/(?P<type>\w+)/(?P<id>[\w-]+)")

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " "Chrome/91.0.4472.114 Safari/537.36"
)

proxy_file = CONFIG_PATH / "http_proxies.txt"

PROXIES: list[str] = list(filter(bool, proxy_file.read_text().split())) if proxy_file.exists() else []


def load_proxy() -> None:
    global PROXIES
    PROXIES = list(filter(bool, proxy_file.read_text().split())) if proxy_file.exists() else []


def del_proxy(proxy: str) -> None:
    try:
        PROXIES.pop(PROXIES.index(proxy.rsplit("/", 1)[-1]))
        logger.info("Deleted proxy %r", proxy)
    except ValueError:
        pass


def save_proxy() -> None:
    proxy_file.write_text("\n".join(PROXIES))


async def make_proxy_request(session: aiohttp.ClientSession, url: str, params: dict, **kwargs) -> dict | None:
    async def req(proxy) -> None:
        try:
            async with session.get(url, params=params, **kwargs, proxy=proxy) as resp:
                return await resp.json()
        except Exception as e:
            del_proxy(proxy)
            raise e

    load_proxy()
    tasks = [asyncio.create_task(req(proxy)) for p in PROXIES for proxy in ["http://" + p, "https://" + p]]
    try:
        for completed_task in asyncio.as_completed(tasks):
            # noinspection PyBroadException
            try:
                res = await completed_task
                if isinstance(res, dict) and res.get("status") != "fail":
                    return res
            except Exception:
                pass
        return None
    finally:
        save_proxy()


class Parser(BaseParser):
    TYPE = ParserType.INSTAGRAM
    REG_EXPS = [
        # https://www.instagram.com/p/CTQZ5Y8J8ZU/
        # https://www.instagram.com/reel/CTQZ5Y8J8ZU/
        # https://instagram.com/reel/CqQGB-1ISIw/
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
        cache: MediaCache,
    ) -> list[Media]:
        post_id = match.group("id")
        post_type = match.group("type")

        original_url = f"https://www.instagram.com/{post_type}/{post_id}"

        await cache.find_by_original_url(original_url)

        variables = {
            "shortcode": post_id,
            "child_comment_count": 3,
            "fetch_comment_count": 40,
            "parent_comment_count": 24,
            "has_threaded_comments": False,
        }

        params = {
            "query_hash": "477b65a610463740ccdb83135b2014db",
            "variables": json.dumps(variables, separators=(",", ":")),
        }

        async with session.get(
            "https://www.instagram.com/graphql/query/",
            params=params,
            headers={"User-Agent": USER_AGENT},
        ) as response:
            data: dict = await response.json()

        if data.get("status") == "fail" and LAMADAVA_SAAS_TOKEN:
            return await cls.get_media_from_saas(
                session=session,
                cache=cache,
                media_code=post_id,
                original_url=original_url,
            )

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
                    for node in shortcode_media.get("edge_media_to_caption", {}).get("edges", [])
                ]
            ).strip()
        url: str | None = shortcode_media.get("video_url", None)
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
            video_width=shortcode_media.get("dimensions", {}).get("width", None),
            video_height=shortcode_media.get("dimensions", {}).get("height", None),
            video_duration=int(shortcode_media.get("video_duration", "0")) or None,
        )
        return await cache.save_group([video])

    @classmethod
    async def get_media_from_saas(
        cls,
        session: aiohttp.ClientSession,
        cache: MediaCache,
        media_code: str,
        original_url: str,
    ) -> list[Media]:
        if not LAMADAVA_SAAS_TOKEN:
            return []
        logger.info("Using lamadava saas for %r", original_url)

        async with session.get(
            "https://api.lamadava.com/v1/media/by/code",
            params={"code": media_code},
            headers={"x-access-key": LAMADAVA_SAAS_TOKEN},
        ) as resp:
            if resp.status != 200:
                logger.error("Error: %s %s", resp.status, await resp.text())
                return []
            data: dict = await resp.json()

        logger.info("Got data: %s", data)
        if not data:
            return []

        url: str | None = data.get("video_url", None)
        if not url:
            logger.info("%s is not a video", original_url)
            return []

        caption = data.get("title", None) or data.get("caption_text", None)

        thumbnail_url = data.get("thumbnail_url", None)
        video_meta = data.get("video_versions", [{}])[0]
        video = Video(
            caption=caption or None,
            type=cls.TYPE,
            original_url=original_url,
            thumbnail_url=thumbnail_url,
            author=data.get("user", {}).get("username", None),
            url=url,
            mime_type="video/mp4",
            video_width=video_meta.get("width", None),
            video_height=video_meta.get("height", None),
            video_duration=int(data.get("video_duration", 0)) or None,
        )
        return await cache.save_group([video])


if __name__ == "__main__":

    async def main() -> None:
        async with aiohttp.ClientSession() as session:
            print(
                await Parser.parse(
                    session,
                    "https://instagram.com/reel/CqQGB-1ISIw/",
                )
            )

    asyncio.run(main())
