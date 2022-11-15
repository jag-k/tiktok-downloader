import logging
import re
from typing import Match, Literal

import aiohttp
from aiohttp import ClientSession

from app import constants
from app.parsers.base import Parser as BaseParser, ParserType, Video, Media, \
    MediaGroup
import logging
import re
from typing import Match, Literal

import aiohttp
from aiohttp import ClientSession

from app import constants
from app.parsers.base import Parser as BaseParser, ParserType, Video, Media, \
    MediaGroup

logger = logging.getLogger(__name__)

TT_USER_AGENT = (
    "com.ss.android.ugc.trill/2613 "
    "(Linux; U; Android 10; en_US; Pixel 4; Build/QQ3A.200805.001; "
    "Cronet/58.0.2991.0)"
)


class Parser(BaseParser):
    TYPE = ParserType.TIKTOK
    REG_EXPS = [
        # https://vt.tiktok.com/ZSRq1jcrg/
        # https://vm.tiktok.com/ZSRq1jcrg/
        re.compile(
            r"(?:https?://)?"
            r"(?:(?P<domain>[a-z]{2})\.)?tiktok\.com/(?P<id>\w+)/?"
        ),

        # https://www.tiktok.com/@thejoyegg/video/7136001098841591041
        re.compile(
            r"(?:https?://)?"
            r"(?:www.)?tiktok\.com/@(?P<author>\w+)/video/(?P<video_id>\d+)/?"
        )
    ]
    CUSTOM_EMOJI_ID = 5465416081105493315  # 📹

    @classmethod
    def _is_supported(cls) -> bool:
        return True

    @classmethod
    async def _parse(
            cls,
            session: aiohttp.ClientSession,
            match: Match
    ) -> list[Media]:
        m = match.groupdict({})
        try:
            url_id = m.get('id')
            if not url_id:
                raise IndexError
            domain = m.get('domain', 'vm')
            original_url = f"https://{domain}.tiktok.com/{url_id}"
            logger.info("Get video id from: %s", original_url)
            video_id: int = await cls._get_video_id(original_url)

        except IndexError:
            nickname = m.get('author')
            video_id: int = int(m.get('video_id'))
            original_url = (
                f"https://www.tiktok.com/@{nickname}/video/{video_id}"
            )

        logger.info(
            "Getting video link from: %s (video_id=%d)",
            original_url,
            video_id,
        )

        try:
            data: dict = await cls._get_video_data(video_id)

        except Exception as e:
            logger.exception(
                'Error while getting video data: %s', original_url,
                exc_info=e,
            )
            return []

        media_type: Literal['video', 'image', None] = data.get('type', None)
        logger.info('Media type: %s', media_type)
        if media_type == 'video':
            return cls._process_video(data, original_url)
        elif media_type == 'image':
            return cls._process_image(data, original_url)
        return []

    @staticmethod
    def _process_video(data: dict, original_url: str) -> list[Video]:
        max_quality_url = data.get('video_data', {}).get('nwm_video_url_HQ')
        url = max(
            filter(
                lambda x: x.get('data_size', 0) <= constants.TG_FILE_LIMIT,
                map(
                    lambda x: x.get('play_addr', {}),
                    data
                    .get('video', {})
                    .get('bit_rate', [])
                ),
            ),
            key=lambda x: x.get('data_size', 0),
        ).get('url_list', [None])[0]

        if not url:
            logger.info('No url in response')
            return []

        caption: str | None = data.get('desc', None)
        thumbnail_url: str | None = (
            data
            .get('cover_data', {})
            .get('origin_cover', {})
            .get('url_list', [None])[0]
        )
        author: str | None = data.get('author', {}).get('nickname', None)
        language: str | None = data.get('region', None)

        video = Video(
            url=url,
            type=ParserType.TIKTOK,
            caption=caption,
            thumbnail_url=thumbnail_url,
            author=author,
            original_url=original_url,
            language=language,
            max_quality_url=max_quality_url,
        )
        if video:
            return [video]

    @staticmethod
    def _process_image(data: dict, original_url: str) -> list[MediaGroup]:
        return []

    @classmethod
    async def _get_video_id(cls, url: str) -> int | None:
        async with ClientSession() as session:
            async with session.get(url, allow_redirects=False) as resp:
                if resp.status == 301:
                    return int(
                        resp.headers['Location']
                        .split('?', 1)[0]
                        .rsplit('/', 1)[-1]
                    )
            async with session.get(url) as resp:
                return int(
                    resp.url
                    .split('?', 1)[0]
                    .rsplit('/', 1)[-1]
                )

    @staticmethod
    async def _get_video_data(video_id: int) -> dict:
        async with ClientSession(
                headers={
                    "Accept": "application/json",
                    "User-Agent": TT_USER_AGENT,
                }
        ) as session:
            async with session.get(
                    "https://api-h2.tiktokv.com/aweme/v1/feed/",
                    params={
                        "aweme_id": video_id,
                        "version_code": 2613,
                        "aid": 1180,
                    },
            ) as resp:
                raw_data: dict = await resp.json()
        if not raw_data.get('aweme_list', []):
            logger.info('No aweme_list in response')
            return {}
        data = raw_data['aweme_list'][0]
        url_type_code = data['aweme_type']
        url_type = 'video' if url_type_code in (0, 4) else 'image'

        api_data = {
            'type': url_type,
            'aweme_id': video_id,
            'cover_data': {
                'cover': data['video']['cover'],
                'origin_cover': data['video']['origin_cover'],
                'dynamic_cover': (
                    data['video']['dynamic_cover']
                    if url_type == 'video'
                    else None
                )
            },
            'hashtags': data.pop('text_extra')
        }

        if url_type == 'video':
            wm_video = data['video']['download_addr']['url_list'][0]
            api_data['video_data'] = {
                'wm_video_url': wm_video,
                'wm_video_url_HQ': wm_video,
                'nwm_video_url': (
                    data['video']['play_addr']['url_list'][0]
                ),
                'nwm_video_url_HQ': (
                    data['video']['bit_rate'][0]['play_addr']['url_list'][0]
                )
            }

        elif url_type == 'image':
            no_watermark_image_list = []
            watermark_image_list = []

            for i in data['image_post_info']['images']:
                no_watermark_image_list.append(
                    i['display_image']['url_list'][0]
                )

                watermark_image_list.append(
                    i['owner_watermark_image']['url_list'][0]
                )

            api_data['image_data'] = {
                'no_watermark_image_list': no_watermark_image_list,
                'watermark_image_list': watermark_image_list
            }
        return data | api_data
