import logging
import os
import traceback
import uuid

import aiohttp as aiohttp
import pytz
from telegram import Update, InlineQueryResultVideo, InlineQueryResult
from telegram.constants import MessageEntityType, ParseMode, ChatType
from telegram.error import BadRequest
from telegram.ext import Application, ContextTypes, \
    MessageHandler, InlineQueryHandler, filters, Defaults, PicklePersistence

from app import commands, settings
from app.constants import DATA_PATH
from app.context import CallbackContext
from app.parsers import Parser, Video, MediaGroup, Media

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TG_TOKEN")
PORT = int(os.environ.get('PORT', '8443'))
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
APP_NAME = os.getenv(
    'APP_NAME',
    f"https://{HEROKU_APP_NAME}.herokuapp.com/",
)


async def link_parser(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
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
                f" from {media.language_emoji}"
                if media.language_emoji
                else ""
            )
            logger.info("Sending video%s: %s", _from_location, media)
            try:
                res = await update.message.reply_video(
                    video=media.url,
                    caption=media.caption,
                    supports_streaming=True,

                )
                if media.update:
                    await media.update(update, res, ctx)
            except BadRequest:
                logger.error("Error sending video: %s", media.url)
                if update.effective_chat.type == ChatType.PRIVATE:
                    logger.info("Sending video as link: %s", media)
                    await update.message.reply_text(
                        f'Error sending video: {media.caption}\n'
                        f'\n\n'
                        f'<a href="{media.url}">Direct link to video</a>',
                        # f'\n\nLink to original video: {media.original_url}',
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
                                f"{video.extra_description}"
                                if video.extra_description
                                else f"by @{video.author} "
                            )
                            if video.author
                            else ''
                        ) + f"from {video.type}",
        )
        for video in medias
        if isinstance(video, Video)
    ]


async def inline_query(update: Update, ctx: CallbackContext):
    """Handle the inline query."""
    query = update.inline_query.query
    history: list[Media] = ctx.history
    logger.info('history: %s', history)

    if not query:
        logger.info(await update.inline_query.answer(
            inline_query_video_from_media(history[::-1]),
            is_personal=True,
            switch_pm_text='Recently added',
            switch_pm_parameter='start',
        ))
        return

    logger.info("Inline query: %s", query)

    async with aiohttp.ClientSession() as session:
        medias: list[Media] = await Parser.parse(session, query)

    logger.info("Medias: %s", medias)
    if not medias:
        logger.info(await update.inline_query.answer(
            inline_query_video_from_media(history[::-1]),
            is_personal=True,
            switch_pm_text='Recently added',
            switch_pm_parameter='start',
        ))
        return

    for media in medias:
        if media not in history:
            history.append(media)
    ctx.user_data['history'] = history

    results: list[InlineQueryResult] = inline_query_video_from_media(medias)
    await update.inline_query.answer(results)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    traceback.print_tb(context.error.__traceback__)


def main() -> None:
    """Start the bot."""
    logger.info("Token: %r", TOKEN)
    persistence = PicklePersistence(filepath=DATA_PATH / "persistence.pickle")
    defaults = Defaults(
        parse_mode=ParseMode.HTML,
        tzinfo=pytz.timezone(os.getenv('TZ', 'Europe/Moscow')),
    )
    application = (
        Application
        .builder()
        .persistence(persistence)
        .defaults(defaults=defaults)
        .token(TOKEN)
        .context_types(ContextTypes(context=CallbackContext))
        .build()
    )

    # on different commands - answer in Telegram
    commands.connect_commands(application)

    # on non command i.e. message - echo the message on Telegram
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(settings.callback_handler())
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, link_parser)
    )

    # Run the bot until the user presses Ctrl-C
    # log all errors
    application.add_error_handler(error)
    if HEROKU_APP_NAME:
        logger.info("Starting webhook on %s", APP_NAME)
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=APP_NAME + TOKEN
        )
    else:
        application.run_polling()


if __name__ == "__main__":
    main()
