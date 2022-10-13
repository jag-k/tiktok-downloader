import logging
import os
import re

import aiohttp as aiohttp
from telegram import Update
from telegram.constants import MessageEntityType
from telegram.ext import Application, CommandHandler, ContextTypes, \
    MessageHandler, filters
from telegram.helpers import create_deep_linked_url

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
# TWITTER_API_KEY_SECRET = os.getenv("TWITTER_API_KEY_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

PORT = int(os.environ.get('PORT', '8443'))

HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

APP_NAME = os.getenv(
    'APP_NAME',
    f"https://{HEROKU_APP_NAME}.herokuapp.com/",
)

# https://vt.tiktok.com/ZSRq1jcrg/
TIKTOK_RE = re.compile(
    r"(?:https?://)?(?:\w{,2}\.)?tiktok\.com/(?P<id>\w+)/?"
)

# https://vt.tiktok.com/ZSRq1jcrg/
TIKTOK_VIDEO_RE = re.compile(
    r"(?:https?://)?(?:www.)?tiktok\.com/(?P<id>\w+)/?"
)

# https://twitter.com/Yoda4ever/status/1580304802608726016?t=FZclIsr-YgDvIIZdbL9pqg&s=35
# https://twitter.com/Yoda4ever/status/1580304802608726016
TWITTER_RE = re.compile(
    r"(?:https?://)?(?:\w{,3}\.)?twitter\.com/(?P<user>\w+)/status/(?P<id>\d+)"
)

''


async def get_tiktok_url_video(
        session: aiohttp.client.ClientSession,
        url: str
) -> str | None:
    """Get TikTok video from url."""
    logger.info("Getting video link from: %s", url)
    async with session.get(
            "https://api.douyin.wtf/api", params={"url": url}
    ) as response:
        data = await response.json()
    return data.get("nwm_video_url", None)


async def get_tweet_videos(
        session: aiohttp.client.ClientSession,
        tweet_id: str
) -> list[str]:
    """Get video from Tweet ID."""

    logger.info(
        "Getting video link from: https://twitter.com/i/status/%s", tweet_id
    )
    async with session.get(
            f"https://api.twitter.com/2/tweets/{tweet_id}",
            params={
                "media.fields": ','.join(("type", "variants")),
                "expansions": "attachments.media_keys",
            },
            headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    ) as response:
        data = await response.json()
    medias = data.get("includes", {}).get("media", [])

    return [
        max(
            media.get('variants', []), key=lambda x: x.get("bit_rate", 0)
        ).get("url")
        for media in medias
        if not print(media)
        if media.get('type') == 'video'
    ]


# Define a few command handlers. These usually take the two arguments update
# and context.
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
    tiktok_links: list[str] = []
    tweets_ids: list[str] = []

    text = update.message.text
    message_links = [
        text[entity.offset:entity.offset + entity.length]
        for entity in update.message.entities
        if entity.type == MessageEntityType.URL
    ]
    for msg_link in message_links:
        tt_link_match = TIKTOK_RE.match(msg_link)
        tw_link_match = TWITTER_RE.match(msg_link)
        if tt_link_match:
            link = f"https://vm.tiktok.com/{tt_link_match.group('id')}"
            if link not in tiktok_links:
                tiktok_links.append(link)
            continue

        if tw_link_match:
            tweets_ids.append(tw_link_match.group('id'))

    async with aiohttp.client.ClientSession() as session:
        video_links: list[str] = [
            video
            for link in tiktok_links
            if (video := await get_tiktok_url_video(session, link))
        ]

        for tweet_id in tweets_ids:
            tweet_video_links = await get_tweet_videos(session, tweet_id)
            if tweet_video_links:
                video_links.extend(tweet_video_links)

    for video in video_links:
        logger.info("Sending video: %s", video)
        await update.message.reply_video(video)


def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    TOKEN = os.getenv("TG_TOKEN")
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
