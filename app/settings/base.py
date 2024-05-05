import contextvars
import logging
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, Generic, TypeVar, Union

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType
from telegram.ext import CallbackQueryHandler, CommandHandler

from app.constants import Keys
from app.context import CallbackContext, ContextSettings
from app.utils import Str
from app.utils.i18n import _

BASE_SETTINGS_ID = "settings"
SETTINGS_SEPARATOR = ":"

_KEY_TYPE = TypeVar("_KEY_TYPE")

logger = logging.getLogger(__name__)


class Settings:
    BOOL_DISPLAY_DICT = {
        True: "✅",
        False: "❌",
    }

    class Context(Generic[_KEY_TYPE]):
        def __init__(
            self,
            settings: "Settings",
            id_: str | Keys,
            context: CallbackContext,
            update: Update,
            parent: str | None = None,
            result: str | None = None,
            settings_data_key: Keys | None = None,
            settings_data_default: _KEY_TYPE | None = None,
        ):
            self.ctx = context
            self.update = update
            self.result = result
            self._id = id_
            self.parent = parent
            self.settings: Settings = settings
            self.settings_data_key = settings_data_key or id_ or self.current
            self.settings_data_default = settings_data_default
            self._context_vars: dict[contextvars.ContextVar, contextvars.Token] = {}

        @property
        def current(self) -> str:
            return f"{self.back}{SETTINGS_SEPARATOR}{self._id}"

        @property
        def back(self) -> str:
            return self.parent or BASE_SETTINGS_ID

        @property
        def home(self) -> str:
            return BASE_SETTINGS_ID

        @property
        def children(self) -> dict[str, "Settings.SubSettings"]:
            return {key: sub for key, sub in self.settings._settings.items() if key.startswith(f"{self.current}:")}

        def update_context_var_token(self, var: contextvars.ContextVar, token: contextvars.Token) -> None:
            self._context_vars[var] = token

        def update_context_var(self, var: contextvars.ContextVar, value: Any) -> None:
            return self.update_context_var_token(var, var.set(value))

        def reset_context_vars(self) -> None:
            for var, token in self._context_vars.items():
                var.reset(token)

        async def update_message(
            self,
            text: str,
            buttons: list[InlineKeyboardButton],
            add_back_button: bool = True,
            columns: int = 2,
        ):
            _buttons: list[list[InlineKeyboardButton]] = [[]]
            for b in buttons:
                if len(_buttons[-1]) == columns:
                    _buttons.append([])
                _buttons[-1].append(b)

            if add_back_button:
                _buttons.insert(0, [self.back_button])
            await self.update.callback_query.answer()

            reply_markup = InlineKeyboardMarkup(_buttons)
            cq = self.update.callback_query
            msg: telegram.Message | None = cq.message
            if not msg:
                return msg

            if msg.text_html != text:
                return await cq.edit_message_text(text=text, reply_markup=reply_markup)
            if msg.reply_markup != reply_markup:
                return await cq.edit_message_reply_markup(reply_markup=reply_markup)
            return msg

        def btn(self, text: str, result: str | None = None) -> InlineKeyboardButton:
            return InlineKeyboardButton(
                text=text,
                callback_data=(f"{self.current}={result}" if result else self.current),
            )

        async def update_message_with_boolean_btn(self, text) -> telegram.Message | None:
            def add_check(v: bool) -> str:
                return "☑️ " if v else ""

            return await self.update_message(
                text=text,
                buttons=[
                    self.btn(
                        text=add_check(self.data) + _("On"),
                        result="on",
                    ),
                    self.btn(
                        text=add_check(not self.data) + _("Off"),
                        result="off",
                    ),
                ],
            )

        async def query_answer(self, text: str, return_to: str | None = None) -> None:
            await self.update.callback_query.answer(text=text)
            return return_to or self.current

        @property
        def data(self) -> _KEY_TYPE:
            return self.ctx.settings[self.settings_data_key]

        @data.setter
        def data(self, value: _KEY_TYPE) -> None:
            self.ctx.settings[self.settings_data_key] = value

        @property
        def back_button(self) -> InlineKeyboardButton:
            return InlineKeyboardButton(text=_("⬅️ Back"), callback_data=self.back)

        def __str__(self) -> str:
            return self.current + (f"={self.result}" if self.result else "")

    class SubSettings(Generic[_KEY_TYPE]):
        def __init__(
            self,
            func: Callable,
            base_settings: "Settings",
            parent: Union[str, "Settings.Context"] = BASE_SETTINGS_ID,
            display_name: Str | None = None,
            settings_data_key: Keys | None = None,
            settings_data_default: _KEY_TYPE | None = None,
            short_display: dict[_KEY_TYPE, Str] | Callable[[_KEY_TYPE], Str] = None,
            display_in_chat: bool = True,
        ):
            self.func = func
            self._settings = base_settings
            self.display_name = display_name or (getattr(func, "__name__", "unknown").replace("_", " ").title().strip())
            self._id: str = getattr(func, "__name__", self.display_name.lower().replace(" ", "_"))
            self.parent = parent if isinstance(parent, str) else parent.current
            self.settings_data_key = settings_data_key or self._id
            self.settings_data_default = settings_data_default
            self.short_display = short_display or {}
            self.display_in_chat = display_in_chat

        @property
        def full_id(self) -> str:
            return f"{self.parent}{SETTINGS_SEPARATOR}{self.id}"

        @property
        def id(self) -> str:
            return self._id

        async def __call__(
            self,
            update: Update,
            context: Union[CallbackContext, "Settings.Context"],
        ):
            __, *res = update.callback_query.data.split("=", 1)
            ctx: Settings.Context

            if isinstance(context, Settings.Context):
                ctx = context
            else:
                ctx = Settings.Context(
                    self._settings,
                    self.id,
                    context,
                    update,
                    self.parent,
                    result=res[0] if res else None,
                    settings_data_key=self.settings_data_key,
                    settings_data_default=self.settings_data_default,
                )
            result = await self.func(ctx)
            ctx.result = None

            if result is None or isinstance(result, int | float | bool):
                return result

            if isinstance(result, Settings.SubSettings):
                result = result.full_id

            r: Settings.SubSettings | None = self._settings._settings.get(result.split("=", 1)[0], None)

            if r is None:
                return await update.callback_query.answer(_("Not implemented yet"))

            try:
                return await r(update, ctx)
            finally:
                ctx.reset_context_vars()

        def add_settings(self, display_name: str | None = None) -> Callable[[Callable], "Settings.SubSettings"]:
            return self._settings.add_settings(display_name=display_name, parent=self.full_id)

    def __init__(self, settings_title: str | None = None) -> None:
        if settings_title is None:

            async def settings_title(update: Update, __: CallbackContext) -> str:
                if update.effective_chat.type == ChatType.PRIVATE:
                    return _("Settings for user {mention}").format(mention=update.effective_user.mention_html())
                return _('Settings for chat "{title}"').format(title=update.effective_chat.title)

        self.settings_title: Str | Callable[[Update, CallbackContext], Awaitable[Str]] = settings_title
        self._settings: dict[str, Settings.SubSettings] = {BASE_SETTINGS_ID: self._base_settings}

    def add_settings(
        self,
        display_name: Str | None = None,
        settings_data_key: Keys | None = None,
        settings_data_default: _KEY_TYPE | None = None,
        short_display: dict[_KEY_TYPE, Str] | Callable[[_KEY_TYPE], Str] = None,
        display_in_chat: bool = True,
        parent: str | Context = BASE_SETTINGS_ID,
    ) -> Callable[[Callable], SubSettings]:
        def wrap(
            func: Callable[[Settings.Context], Coroutine[..., ..., str | None]],
        ) -> Settings.SubSettings:
            sub = self.SubSettings(
                func=func,
                base_settings=self,
                parent=parent,
                display_name=display_name,
                settings_data_key=settings_data_key,
                settings_data_default=settings_data_default,
                short_display=short_display,
                display_in_chat=display_in_chat,
            )
            logger.info("Adding settings %s", sub.full_id)
            ContextSettings.DEFAULTS[sub.settings_data_key] = sub.settings_data_default

            self._settings[sub.full_id] = sub
            return sub

        return wrap

    def add_bool_settings(
        self,
        display_name: str | None = None,
        settings_data_key: Keys | None = None,
        settings_data_default: bool = False,
        parent: str | Context = BASE_SETTINGS_ID,
    ) -> Callable[[Callable], SubSettings]:
        return self.add_settings(
            display_name=display_name,
            settings_data_key=settings_data_key,
            settings_data_default=settings_data_default,
            short_display=Settings.BOOL_DISPLAY_DICT,
            parent=parent,
        )

    def bool_settings_template(
        self,
        id_: str | Keys,
        template_str_answer: Str,
        template_str_menu: Str,
        display_name: str | None = None,
        settings_data_key: str | None = None,
        settings_data_default: bool = False,
        parent: str | Context = BASE_SETTINGS_ID,
    ) -> SubSettings:
        settings_data_key = settings_data_key or id_

        async def wrap(ctx: Settings.Context[bool]) -> None:
            if ctx.result:
                ctx.data = ctx.result == "on"
                return await ctx.query_answer(
                    template_str_answer.format(_("enabled ✅") if ctx.data else _("disabled ❌"))
                )

            await ctx.update_message_with_boolean_btn(
                template_str_menu.format(_("✅ <b>Enabled</b>") if ctx.data else _("❌ <b>Disabled</b>"))
            )

        wrap.__name__ = id_.value if isinstance(id_, Keys) else id_
        return self.add_bool_settings(
            display_name=display_name,
            settings_data_key=settings_data_key,
            settings_data_default=settings_data_default,
            parent=parent,
        )(wrap)

    async def _base_settings(self, update: Update, context: CallbackContext) -> telegram.Message:
        send_text = (
            update.callback_query.edit_message_text
            if update.callback_query and update.callback_query.message
            else update.message.reply_text
        )

        if update.callback_query:
            await update.callback_query.answer()

        buttons: list[InlineKeyboardButton] = []
        for id_, sub in self._settings.items():
            if id_ == BASE_SETTINGS_ID or not sub.display_in_chat:
                continue

            current_data = context.settings.get(sub.settings_data_key, sub.settings_data_default)
            sdd = sub.short_display

            display_current_data = sdd(current_data) if callable(sdd) else sdd.get(current_data)

            buttons.append(
                InlineKeyboardButton(
                    (f"{sub.display_name}: {display_current_data}" if display_current_data else sub.display_name.s),
                    callback_data=id_,
                )
            )

        title = self.settings_title
        if callable(title):
            title = await title(update, context)

        return await send_text(
            title,
            reply_markup=InlineKeyboardMarkup.from_column(buttons),
        )

    async def callback(self, update: Update, context: CallbackContext) -> bool:
        data, *__ = update.callback_query.data.strip().lower().split("=", 1)
        func = self._settings.get(data)
        if callable(func):
            return await func(update, context)
        return await update.callback_query.answer(_("Not implemented yet"))

    def command_handler(self, command: str = BASE_SETTINGS_ID) -> CommandHandler:
        return CommandHandler(command, self._base_settings)

    def callback_handler(self) -> CallbackQueryHandler:
        return CallbackQueryHandler(self.callback, pattern=f"^{BASE_SETTINGS_ID}")
