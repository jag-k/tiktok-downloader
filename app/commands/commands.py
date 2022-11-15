from telegram import Update
from telegram.helpers import create_deep_linked_url

from app import constants, settings
from app.commands.registrator import CommandRegistrator
from app.context import CallbackContext
from app.parsers.base import Parser

commands = CommandRegistrator()


def start_text() -> str:
    services: list[str] = [i.TYPE for i in Parser.parsers() if i.TYPE]
    services_str = " or ".join((", ".join(services[:-1]), services[-1]))
    return (
        f"Send me a link to a {services_str} video and "
        f"I'll send this video back to you.\n\n"
        f"Also, you can use me in groups. "
        f"Just add me to the group and send a link to a video."
    )


@commands.add(description="Start using the bot")
async def start(update: Update, ctx: CallbackContext) -> None:
    await update.message.reply_html(
        f"{start_text()}\n\nUse /help to get more information.",
    )
    await commands.send_commands(update, ctx)


@commands.add('help', "Get more information about the bot.")
async def help_command(update: Update, ctx: CallbackContext) -> None:
    link = create_deep_linked_url(ctx.bot.username, 'start', group=True)
    cmds = commands.get_command_description().get(constants.DEFAULT_LOCALE)
    supported_commands = '\n'.join(
        f"- /{command} - {description}"
        for command, description in cmds.items()
    )
    contacts = ''
    if constants.CONTACTS:
        contacts = "\n\nContacts:" + '\n'.join(
            f'{c["type"]}: <a href="{c["link"]}">{c["name"]}</a>'
            for c in constants.CONTACTS
            if all(map(c.get, ('type', 'link', 'name')))
        )
    await update.message.reply_text(
        f"{start_text()}\n\n"
        f"Link to add in groups: {link}\n\n"
        f"Supported Commands:\n"
        f"{supported_commands}\n\n"
        f"Inline queries are supported.\n"
        f"Use @{ctx.bot.username} in any chat to get started.\n"
        f"To get history of your inline queries, "
        f"set empty after mention bot (or add some spaces).\n"
        f"To get video from inline query, "
        f"add link to video after mention bot.\n"
        f"{contacts}"
    )


@commands.add()
async def clear_history(update: Update, ctx: CallbackContext) -> None:
    """Clear your history from inline queries."""
    ctx.history = []
    await update.message.reply_text("History cleared.")


# commands.add_handler(settings.command_handler(), "Bot settings")
