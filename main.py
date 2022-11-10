import logging
import os
import uuid
from pathlib import Path

import aiohttp as aiohttp
import pytz
from telegram import Update, InlineQueryResultVideo, InlineQueryResult
from telegram.constants import MessageEntityType, ParseMode, ChatType
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, ContextTypes, \
    MessageHandler, InlineQueryHandler, filters, Defaults, PicklePersistence
from telegram.helpers import create_deep_linked_url

BASE_PATH = (
    Path(__file__).resolve().parent
    if os.getenv('BASE_PATH') is None
    else Path(os.getenv('BASE_PATH'))
)

CONFIG_PATH = BASE_PATH / 'config'
DATA_PATH = BASE_PATH / 'config'

ENV_PATHS = [
    BASE_PATH / '.env',
    BASE_PATH / '.env.local',
    CONFIG_PATH / '.env',
    CONFIG_PATH / '.env.local',
]

for env_path in ENV_PATHS:
    if env_path and env_path.exists() and env_path.is_file():
        from dotenv import load_dotenv

        load_dotenv(env_path)
        print(f"Loaded env from {env_path}")
        break
else:
    print("No .env file found")

from parsers import Parser, Video, MediaGroup, Media

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


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_html(
        f"I'm looking for you 👀",
    )


async def help_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    link = create_deep_linked_url(ctx.bot.username, 'start', group=True)
    await update.message.reply_text(
        f"Just simple download a TikTok and Tweeter video.\n\n"
        f"Link to use in groups: {link}"
    )


async def echo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
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


async def inline_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle the inline query."""
    query = update.inline_query.query
    history = ctx.user_data.get('history', [])
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
        .build()
    )

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(InlineQueryHandler(inline_query))

    # on non command i.e. message - echo the message on Telegram
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, echo)
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
