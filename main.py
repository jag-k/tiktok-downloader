import logging
import traceback
import uuid

import aiohttp as aiohttp
from aiohttp import ClientSession
from telegram import Update, InlineQueryResultVideo, InlineQueryResult
from telegram.constants import MessageEntityType, ParseMode, ChatType
from telegram.error import BadRequest
from telegram.ext import Application, ContextTypes, \
    MessageHandler, InlineQueryHandler, filters, Defaults, PicklePersistence

from app import commands, settings, constants
from app.constants import DATA_PATH
from app.context import CallbackContext
from app.parsers import Parser, Video, MediaGroup, Media
from app.utils import translate_patch_app, a
from app.utils.i18n import _n, _

logger = logging.getLogger(__name__)


async def link_parser(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Parse link from the user message."""
    text = getattr(update.message, "text", "")
    message_links = [
        text[entity.offset:entity.offset + entity.length]
        for entity in update.message.entities
        if entity.type == MessageEntityType.URL
    ]

    async with aiohttp.ClientSession() as session:
        medias: list[Media] = await Parser.parse(session, *message_links)

    for media in medias:
        if isinstance(media, Video):
            _from_location = (
                _(" from {flag}").format(flag=media.language_emoji)
                if media.language_emoji
                else ""
            )
            logger.info("Sending video%s: %s", _from_location, media)
            extra_caption = (
                _(
                    '\n\n\n<i>Original video is larger than <b>20 MB</b>,'
                    ' and bot can\'t send it.</i> '
                    '<a href="{url}">'
                    'This is original link</a>'
                ).format(url=media.max_quality_url)
                if media.max_quality_url and media.max_quality_url != media.url
                else ''
            )
            try:
                try:
                    # async with ClientSession() as session:
                    #     async with session.get(media.url) as resp:
                    #         video_content = await resp.content.read()
                    res = await update.message.reply_video(
                        video=media.url,
                        # video=video_content,
                        caption=media.caption + extra_caption,
                        supports_streaming=True,
                    )
                    if media.update:
                        return await media.update(update, res, ctx)
                    return res
                except BadRequest as e:
                    if e.message == 'Failed to get http url content':
                        async with ClientSession() as session:
                            async with session.get(media.url) as resp:
                                video_content = await resp.content.read()
                        res = await update.message.reply_video(
                            video=video_content,
                            caption=media.caption + extra_caption,
                            supports_streaming=True,
                        )
                        if media.update:
                            return await media.update(update, res, ctx)
                        return res
                    raise e
            except BadRequest as e:
                logger.error(
                    "Error sending video: %s",
                    media.url,
                    exc_info=e,
                    stack_info=True
                )
                if update.effective_chat.type == ChatType.PRIVATE:
                    logger.info("Sending video as link: %s", media)
                    title = a(media.caption, media.original_url)
                    await update.message.reply_text(
                        _(
                            'Error sending video: {title}\n'
                            '\n\n'
                            '<a href="{url}">Direct link to video</a>'
                        ).format(title=title, url=media.url),
                    )
                    logger.info("Send video as link: %s", media.url)
        elif isinstance(media, MediaGroup):
            logger.info("Sending medias from %s", media.original_url)
            i_medias = media.input_medias

            for m in i_medias:
                m.caption = media.caption

            await update.message.reply_media_group(
                media=i_medias,
            )


def inline_query_video_from_media(
    medias: list[Media]
) -> list[InlineQueryResultVideo]:
    return [
        InlineQueryResultVideo(
            id=str(uuid.uuid4()),
            video_url=video.url,
            mime_type=video.mime_type,
            thumb_url=video.thumbnail_url or video.url,
            title=video.caption,
            caption=video.caption,
            description=(
                            (
                                video.extra_description
                                if video.extra_description
                                else _("by @{author} ").format(
                                    author=video.author
                                )
                            )
                            if video.author
                            else ''
                        ) + _("from {m_type}").format(m_type=video.type),
        )
        for video in medias
        if isinstance(video, Video)
    ]


async def inline_query(update: Update, ctx: CallbackContext):
    """Handle the inline query."""
    logger.info("Checking inline query...")
    query = (update.inline_query.query or '').strip()

    async def send_history():
        return await update.inline_query.answer(
            inline_query_video_from_media(ctx.history[::-1]),
            is_personal=True,
            switch_pm_text=_('Recently added').s,
            switch_pm_parameter='help',
        )

    if not query:
        answer = await send_history()
        logger.info('Send history from inline query: %s', answer)
        return answer

    logger.info("Inline query: %s", query)

    async with aiohttp.ClientSession() as session:
        medias: list[Media] = await Parser.parse(session, query)

    logger.info("Medias: %s", medias)
    if not medias:
        answer = await send_history()
        logger.info(
            'No medias found. Send history from inline query: %s',
            answer,
        )
        return

    for media in medias:
        if media not in ctx.history:
            ctx.history.append(media)

    results: list[InlineQueryResult] = inline_query_video_from_media(medias)
    await update.inline_query.answer(
        results,
        switch_pm_text=(
            _n('Found %d video', 'Found %d videos', len(results))
            % str(len(results))
            if results
            else _('No videos found')
        ).s,
        switch_pm_parameter='help',
    )


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    logger.warning(
        '%s: %s. Update: "%s"',
        type(context.error).__name__,
        context.error,
        update,
    )
    traceback.print_tb(context.error.__traceback__)


def main() -> None:
    """Start the bot."""
    logger.debug("Token: %r", constants.TOKEN)
    persistence = PicklePersistence(filepath=DATA_PATH / "persistence.pickle")
    defaults = Defaults(
        parse_mode=ParseMode.HTML,
        tzinfo=constants.TIME_ZONE,
    )
    application = (
        Application
        .builder()
        .persistence(persistence)
        .defaults(defaults=defaults)
        .token(constants.TOKEN)
        .context_types(ContextTypes(context=CallbackContext))
        .build()
    )

    commands.connect_commands(application)
    application.add_handler(settings.callback_handler())
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, link_parser)
    )
    translate_patch_app(application)

    # Run the bot until the user presses Ctrl-C
    # log all errors
    application.add_error_handler(error)
    application.run_polling()


if __name__ == "__main__":
    main()
