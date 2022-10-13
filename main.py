import logging
import os
import uuid

import aiohttp as aiohttp
from telegram import Update, InlineQueryResultVideo
from telegram.constants import MessageEntityType
from telegram.ext import Application, CommandHandler, ContextTypes, \
    MessageHandler, InlineQueryHandler, filters
from telegram.helpers import create_deep_linked_url

from parsers import Video, Parser

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


async def echo(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    text = update.message.text
    message_links = [
        text[entity.offset:entity.offset + entity.length]
        for entity in update.message.entities
        if entity.type == MessageEntityType.URL
    ]
    async with aiohttp.ClientSession() as session:
        videos: list[Video] = await Parser.parse(session, *message_links)

    for video in videos:
        logger.info("Sending video: %s", video)
        await update.message.reply_video(
            video=video.url,
            caption=video.caption,
        )


async def inline_query(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handle the inline query."""
    query = update.inline_query.query
    if not query:
        return

    logger.info("Inline query: %s", query)

    async with aiohttp.ClientSession() as session:
        videos: list[Video] = await Parser.parse(session, query)

    logger.info("Videos: %s", videos)

    results = [
        InlineQueryResultVideo(
            id=str(uuid.uuid4()),
            video_url=video.url,
            mime_type="video/mp4",
            thumb_url=video.thumbnail_url or video.url,
            title=video.caption,
            caption=video.caption,
            description=(
                      f"by @{video.author}"
                      if video.author
                      else ''
                  ) + f"from {video.type}"
        )
        for video in videos
    ]
    return await update.inline_query.answer(results)


def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    logger.info("Token: %r", TOKEN)
    application = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(InlineQueryHandler(inline_query))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, echo)
    )

    # Run the bot until the user presses Ctrl-C
    # log all errors
    application.add_error_handler(error)
    if HEROKU_APP_NAME:
        logger.info("Starting webhook on %s:%s", APP_NAME, PORT)
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
