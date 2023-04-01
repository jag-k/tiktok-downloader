import logging
import re
import traceback
import uuid

import aiohttp as aiohttp
from telegram import (
    InlineQueryResult,
    InlineQueryResultVideo,
    Update,
)
from telegram.constants import ChatType, MessageEntityType, ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    ChosenInlineResultHandler,
    ContextTypes,
    Defaults,
    InlineQueryHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

from app import commands, constants, settings
from app.context import CallbackContext
from app.parsers import Media, MediaGroup, Parser, Video
from app.utils import a, make_caption, notify, patch

# noinspection PyProtectedMember
from app.utils.i18n import _, _n

logger = logging.getLogger(__name__)


async def _process_video(update: Update, ctx: CallbackContext, media: Video):
    caption = make_caption(ctx, "")
    extra_caption = ""
    if media.max_quality_url and media.max_quality_url != media.url:
        extra_caption = _(
            "\n\n\n<i>Original video is larger than <b>20 MB</b>,"
            " and bot can't send it.</i> "
            '<a href="{url}">'
            "This is original link</a>"
        ).format(url=media.max_quality_url)

    media_caption = (caption(media) + extra_caption).strip()

    # try:
    #     res = await update.message.reply_video(
    #         video=media.url,
    #         caption=media_caption,
    #         supports_streaming=True,
    #     )
    #     return await media.update(update, res, ctx)
    # except BadRequest as e:
    try:
        # if e.message != "Failed to get http url content":
        #     raise e
        res = await update.message.reply_video(
            video=(
                ctx.tg_video_cache.get(media.original_url)
                or media.file_input
                or media.url
            ),
            caption=media_caption,
            supports_streaming=True,
            width=media.video_width,
            height=media.video_height,
            duration=media.video_duration,
        )
        ctx.tg_video_cache[media.original_url] = res.video
        return await media.update(update, res, ctx)
    except BadRequest as e:
        logger.error(
            "Error sending video: %s",
            media.url,
            exc_info=e,
            stack_info=True,
        )
        if update.effective_chat.type == ChatType.PRIVATE:
            logger.info("Sending video as link: %s", media)
            await update.message.reply_text(
                _(
                    "Error sending video: {title}\n"
                    "\n\n"
                    '<a href="{url}">Direct link to video</a>'
                ).format(
                    title=a(media_caption, media.original_url),
                    url=media.url,
                ),
            )
            logger.info("Send video as link: %s", media.url)


async def _process_media_group(
    update: Update, _: CallbackContext, media: MediaGroup
):
    i_medias = media.input_medias

    for m in i_medias:
        m.caption = media.caption

    await update.message.reply_media_group(
        media=i_medias,
    )


async def link_parser(update: Update, ctx: CallbackContext):
    """Parse link from the user message."""
    text = getattr(update.message, "text", "")
    message_links = [
        text[entity.offset : entity.offset + entity.length]
        for entity in update.message.entities
        if entity.type == MessageEntityType.URL
    ]

    async with aiohttp.ClientSession() as session:
        medias: list[Media] = await Parser.parse(
            session, *message_links, cache=ctx.media_cache
        )

    for media in medias:
        if isinstance(media, Video):
            _from_location = (
                f" from {media.language_emoji}" if media.language_emoji else ""
            )
            logger.info("Sending video%s: %s", _from_location, media)
            return await _process_video(update, ctx, media)

        if isinstance(media, MediaGroup):
            logger.info("Sending medias from %s", media.original_url)
            return await _process_media_group(update, ctx, media)


def inline_query_description(video: Video) -> str:
    resp = ""
    if video.author:
        if video.extra_description:
            resp += video.extra_description
        else:
            resp += _("by @{author} ").format(author=video.author)
    resp += _("from {m_type}").format(m_type=video.type)
    if video.language:
        resp += f" {video.language_emoji}"
    return resp


async def inline_query_video_from_media(
    medias: list[Media],
    ctx: CallbackContext,
) -> list[InlineQueryResultVideo]:
    caption = make_caption(ctx)

    def content(media: Video) -> InlineQueryResultVideo:
        c = media.caption
        if media.video_content:
            ctx.media_cache[media.original_url] = media

        if not c:
            c = _("{m_type} video").format(m_type=media.type.value)

        return InlineQueryResultVideo(
            id=str(uuid.uuid4()),
            video_url=media.url,
            mime_type=media.mime_type,
            thumbnail_url=media.thumbnail_url or media.url,
            title=c,
            caption=caption(media),
            description=inline_query_description(media),
            video_width=media.video_width,
            video_height=media.video_height,
            video_duration=media.video_duration,
        )

    return [content(media) for media in medias if isinstance(media, Video)]


async def chosen_inline_query(update: Update, ctx: CallbackContext):
    video = ctx.temp_history.pop(update.chosen_inline_result.result_id, None)
    logger.info("Chosen video: %s", video)
    ctx.temp_history.clear()

    if video and video not in ctx.history:
        logger.info("Add %s video to history", video)
        ctx.history.append(video)


async def inline_query(update: Update, ctx: CallbackContext):
    """Handle the inline query."""
    logger.info("Checking inline query...")
    query = (update.inline_query.query or "").strip()

    async def send_history():
        return await update.inline_query.answer(
            await inline_query_video_from_media(ctx.history[::-1], ctx),
            is_personal=True,
            switch_pm_text=_("Recently added"),
            switch_pm_parameter="help",
            cache_time=1,
        )

    if not query:
        answer = await send_history()
        logger.info("Send history from inline query: %s", answer)
        return answer

    logger.info("Inline query: %s", query)

    not_found_text = _(
        "No videos found. You don't think it's correct? Press here!"
    )

    async with aiohttp.ClientSession() as session:
        medias: list[Media] = await Parser.parse(
            session, query, cache=ctx.media_cache
        )

    logger.info("Medias: %s", medias)
    if not medias:
        m = re.match(r"https?://(?:www\.)?(.*)", query)
        if m:
            query = m.groups()[0]
        r_query = query.replace("/", "__").replace(".", "--").split("?", 1)[0]
        report = f"report_{r_query}"
        logger.info("No medias found. Report: %s", report)
        return await update.inline_query.answer(
            [],
            is_personal=True,
            switch_pm_text=not_found_text,
            switch_pm_parameter=report,
            cache_time=1,
        )

    results: list[InlineQueryResult] = await inline_query_video_from_media(
        medias, ctx
    )
    for video, iq_video in zip(
        filter(lambda x: isinstance(x, Video), medias), results
    ):
        ctx.temp_history[iq_video.id] = video

    await update.inline_query.answer(
        results,
        is_personal=True,
        switch_pm_text=(
            _n("Found %d video", "Found %d videos", len(results)) % len(results)
            if results
            else not_found_text
        ),
        switch_pm_parameter="help",
        cache_time=1,
    )


async def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    exc = context.error
    logger.warning('%s: %s. Update: "%s"', type(exc).__name__, exc, update)
    traceback.print_tb(context.error.__traceback__)
    await notify.send_message(
        message_type=notify.MessageType.EXCEPTION,
        text=f'{type(exc).__name__}: {exc}. Update: "{update}"',
        update=update,
        ctx=context,
        extras={"exception": exc},
    )


def main() -> None:
    """Start the bot."""
    logger.debug("Token: %r", constants.TOKEN)
    persistence = PicklePersistence(
        filepath=constants.DATA_PATH / "persistence.pickle"
    )
    defaults = Defaults(
        parse_mode=ParseMode.HTML,
        tzinfo=constants.TIME_ZONE,
    )
    application = (
        Application.builder()
        .persistence(persistence)
        .defaults(defaults=defaults)
        .token(constants.TOKEN)
        .context_types(ContextTypes(context=CallbackContext))
        .build()
    )

    application.add_handlers(
        [
            ChosenInlineResultHandler(chosen_inline_query),
            settings.callback_handler(),
            InlineQueryHandler(inline_query),
            MessageHandler(filters.TEXT & ~filters.COMMAND, link_parser),
        ]
    )
    commands.connect_commands(application)
    patch(application)

    # Run the bot until the user presses Ctrl-C
    # log all errors
    application.add_error_handler(error)
    application.run_polling()


if __name__ == "__main__":
    main()
