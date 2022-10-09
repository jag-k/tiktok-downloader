import logging
import os
import re

import aiohttp as aiohttp
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, \
    MessageHandler, filters
from telegram.helpers import create_deep_linked_url

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# https://vt.tiktok.com/ZSRq1jcrg/
TIKTOK_RE = re.compile(
    r"(?:https?://)?(?:\w{,2}\.)?tiktok\.com/(?P<id>\w+)/?"
)


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


# Define a few command handlers. These usually take the two arguments update
# and context.
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_html(
        f"I'm looking for you 👀",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    link = create_deep_linked_url(ctx.bot.username, 'start', group=True)
    await update.message.reply_text(
        f"Just simple download a TikTok video.\n\n"
        f"Link to use in groups: {link}"
    )


async def echo(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    links: list[str] = []

    for link_match in TIKTOK_RE.finditer(update.message.text):
        link = f"https://vm.tiktok.com/{link_match.group('id')}"
        if link not in links:
            links.append(link)

    async with aiohttp.client.ClientSession() as session:
        video_links: list[str] = [
            video
            for link in links
            if (video := await get_tiktok_url_video(session, link))
        ]

    for video in video_links:
        logger.info("Sending video: %s", video)
        await update.message.reply_video(video)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    TOKEN = os.getenv("TOKEN")
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
    application.run_polling()


if __name__ == "__main__":
    main()
