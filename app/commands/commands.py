import logging
import random
from collections.abc import Callable

from telegram import (
    ChatAdministratorRights,
    KeyboardButton,
    KeyboardButtonRequestChat,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ChatType
from telegram.helpers import create_deep_linked_url

from app import constants, settings
from app.commands.registrator import CommandRegistrator
from app.constants import DEFAULT_LOCALE
from app.context import CallbackContext
from app.parsers.base import Parser
from app.utils import a, async_add_report, b
from app.utils.i18n import _

commands = CommandRegistrator()

logger = logging.getLogger(__name__)


def start_text() -> str:
    services: list[str] = [b(i.TYPE) for i in Parser.parsers() if i.TYPE]
    services_str = _(" or ").join((", ".join(services[:-1]), services[-1]))
    return _(
        "Send me a link to a {} video and "
        "I'll send this video back to you.\n\n"
        "Also, you can use me in groups. "
        "Just add me to the group and send a link to a video."
    ).format(services_str)


@commands.add(description=_("Start using the bot"))
async def start(update: Update, ctx: CallbackContext) -> None:
    report = ctx.report_args
    if report:
        await async_add_report(update, report)
        await update.message.reply_html(
            _(
                "Thank you for your report!\n"
                "We will try to fix this issue as soon as possible."
            ).s
        )
        logger.info("Report from %s: %s", update.message.from_user, report)
        return

    await update.message.reply_html(
        _("{}\n\nUse /help to get more information.").format(start_text())
    )


@commands.add("help", _("Get more information about the bot."))
async def help_command(update: Update, ctx: CallbackContext) -> None:
    link = create_deep_linked_url(ctx.bot.username, "start", group=True)
    cmds = commands.get_command_description()
    supported_commands = "\n".join(
        f"- /{command} - {str(description)}"
        for command, description in cmds.items()
    )
    contacts = ""

    def get_by_lang(obj: dict[str, str]) -> Callable[[str], str]:
        def get(key: str) -> str:
            if res := obj.get(f"{key}_{ctx.user_lang}"):
                return res
            if res := obj.get(f"{key}_{ctx.user_lang.split('-')[0]}"):
                return res
            if res := obj.get(f"{key}_{DEFAULT_LOCALE}"):
                return res
            return obj.get(key)

        return get

    if constants.CONTACTS:
        contacts_list = "\n".join(
            f'{g("type")}: {a(g("text"), c.get("url"))}'
            for c in constants.CONTACTS
            if all(map(c.get, ("type", "text")))
            if (g := get_by_lang(c))
        )
        if contacts_list:
            contacts = _("\n\nContacts:\n{contacts_list}").format(
                contacts_list=contacts_list,
            )

    reply_markup = None
    rights = ChatAdministratorRights(
        is_anonymous=False,
        can_manage_chat=True,
        can_delete_messages=False,
        can_manage_video_chats=False,
        can_restrict_members=False,
        can_promote_members=False,
        can_change_info=False,
        can_invite_users=False,
        can_post_messages=True,
        can_edit_messages=True,
    )
    if update.message.chat.type == ChatType.PRIVATE:
        reply_markup = ReplyKeyboardMarkup.from_button(
            button=KeyboardButton(
                text=_("Add to group").s,
                request_chat=KeyboardButtonRequestChat(
                    request_id=random.randint(0, 100000),
                    chat_is_channel=False,
                    user_administrator_rights=rights,
                    bot_administrator_rights=rights,
                    bot_is_member=True,
                ),
            ),
            resize_keyboard=True,
            one_time_keyboard=True,
        )

    await update.message.reply_text(
        _(
            "{}\n\n"
            "Link to add in groups: {}\n\n"
            "Supported Commands:\n"
            "{}\n\n"
            "Inline queries are supported.\n"
            "Use @{} in any chat to get started.\n"
            "To get history of your inline queries, "
            "set empty after mention bot (or add some spaces).\n"
            "To get video from inline query, "
            "add link to video after mention bot.\n"
            "{}"
        ).format(
            start_text(),
            link,
            supported_commands,
            ctx.bot.username,
            contacts,
        ),
        reply_markup=reply_markup,
    )


@commands.add(description=_("Clear your history from inline queries."))
async def clear_history(update: Update, ctx: CallbackContext) -> None:
    ctx.history = []
    await update.message.reply_text(_("History cleared.").s)


commands.add_handler(settings.command_handler(), _("Bot settings"))
