from typing import Callable, Union, TypeVar, Generic

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ChatType
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from app.context import CallbackContext

BASE_SETTINGS_ID = "settings"
SETTINGS_SEPARATOR = ":"

_KEY_TYPE = TypeVar("_KEY_TYPE")


class Settings:
    BOOL_DISPLAY_DICT = {
        True: '✅',
        False: '❌',
    }

    class Context(Generic[_KEY_TYPE]):
        def __init__(
                self,
                settings: 'Settings',
                id_: str,
                context: ContextTypes.DEFAULT_TYPE,
                update: Update,
                parent: str | None = None,
                result: str = None,
                settings_data_key: str = None,
                settings_data_default: _KEY_TYPE | None = None,
        ):
            self.ctx = context
            self.update = update
            self.result = result
            self._id = id_
            self.parent = parent
            self.settings: Settings = settings
            self.settings_data_key = settings_data_key or self.current
            self.settings_data_default = settings_data_default

        @property
        def current(self):
            return f"{self.back}{SETTINGS_SEPARATOR}{self._id}"

        @property
        def back(self) -> str:
            return self.parent or BASE_SETTINGS_ID

        @property
        def home(self) -> str:
            return BASE_SETTINGS_ID

        @property
        def children(self) -> dict[str, 'Settings.SubSettings']:
            return {
                key: sub
                for key, sub in self.settings._settings.items()
                if key.startswith(f"{self.current}:")
            }

        async def update_message(
                self,
                text: str,
                buttons: list[InlineKeyboardButton],
                add_back_button: bool = True,
                columns: int = 2,
        ):
            btns = [[]]
            for b in buttons:
                if len(btns[-1]) == columns:
                    btns.append([])
                btns[-1].append(b)

            if add_back_button:
                btns.insert(0, [self.back_button])
            # await self.update.callback_query.answer(text.split('\n')[0])
            await self.update.callback_query.answer()
            return await self.update.callback_query.message.edit_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(btns)
            )

        def btn(self, text: str, result: str | None = None):
            return InlineKeyboardButton(
                text=text,
                callback_data=(
                    f"{self.current}={result}"
                    if result
                    else self.current
                )
            )

        async def update_message_with_boolean_btn(self, text):
            return await self.update_message(
                text=text,
                buttons=[
                    self.btn(text='On', result='on'),
                    self.btn(text='Off', result='off'),
                ]
            )

        async def query_answer(self, text: str, return_to: str = None):
            await self.update.callback_query.answer(text=text)
            return return_to or self.current

        @property
        def user_data(self):
            return self.ctx.user_data

        @property
        def chat_data(self):
            return self.ctx.chat_data

        @property
        def setting_data(self):
            if self.update.effective_chat.type == ChatType.PRIVATE:
                return self.user_data
            return self.chat_data

        @property
        def data(self) -> _KEY_TYPE:
            return self.setting_data.get(
                self.settings_data_key,
                self.settings_data_default,
            )

        @data.setter
        def data(self, value: _KEY_TYPE):
            self.setting_data[self.settings_data_key] = value

        @property
        def back_button(self):
            return InlineKeyboardButton(
                text="⬅️ Back",
                callback_data=self.back
            )

        def __str__(self):
            return self.current + (
                f"={self.result}" if self.result else ""
            )

    class SubSettings(Generic[_KEY_TYPE]):
        def __init__(
                self,
                func: Callable,
                base_settings: 'Settings',
                parent: Union[str, 'Settings.Context'] = BASE_SETTINGS_ID,
                display_name: str | None = None,
                settings_data_key: str = None,
                settings_data_default: _KEY_TYPE | None = None,
                short_display_dict: (
                        dict[_KEY_TYPE, str]
                        | Callable[[_KEY_TYPE], str]
                ) = None,
                display_in_chat: bool = True,
        ):
            self.func = func
            self._settings = base_settings
            self.display_name = (display_name or (
                getattr(func, '__name__', 'unknown')
                .replace("_", " ")
                .title()
            )).strip()
            self._id = getattr(
                func,
                "__name__",
                self.display_name.lower().replace(" ", "_")
            )
            self.parent = parent if isinstance(parent, str) else parent.current
            self.settings_data_key = settings_data_key or self.full_id
            self.settings_data_default = settings_data_default
            self.short_display_dict = short_display_dict or {}
            self.display_in_chat = display_in_chat

        @property
        def full_id(self):
            return f"{self.parent}{SETTINGS_SEPARATOR}{self.id}"

        @property
        def id(self):
            return self._id

        async def __call__(self,
                           update: Update,
                           context: ContextTypes.DEFAULT_TYPE
                           ):
            _, *res = update.callback_query.data.split("=", 1)
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

            if result is None or isinstance(result, (int, float, bool)):
                return result

            if isinstance(result, Settings.SubSettings):
                result = result.full_id

            r = self._settings._settings.get(result.split("=", 1)[0], None)

            if r is None:
                return await update.callback_query.answer(
                    "Not implemented yet"
                )

            update.callback_query.data = result
            return await r(update, context)

        def add_settings(self, display_name: str = None):
            return self._settings.add_settings(
                display_name=display_name,
                parent=self.full_id
            )

    def __init__(self, settings_title: str = "Settings"):
        self.settings_title = settings_title
        self._settings: dict[str, Settings.SubSettings] = {
            BASE_SETTINGS_ID: self._base_settings
        }

    def add_settings(
            self,
            display_name: str = None,
            settings_data_key: str = None,
            settings_data_default: _KEY_TYPE = None,
            short_display_dict: (
                    dict[_KEY_TYPE, str]
                    | Callable[[_KEY_TYPE], str]
            ) = None,
            display_in_chat: bool = True,
            parent: str | Context = BASE_SETTINGS_ID,
    ):
        def wrap(func: Callable[[Settings.Context], str | None]):
            sub = self.SubSettings(
                func=func,
                base_settings=self,
                parent=parent,
                display_name=display_name,
                settings_data_key=settings_data_key,
                settings_data_default=settings_data_default,
                short_display_dict=short_display_dict,
                display_in_chat=display_in_chat,
            )
            self._settings[sub.full_id] = sub
            return sub

        return wrap

    def add_bool_settings(
            self,
            display_name: str = None,
            settings_data_key: str = None,
            settings_data_default: bool = False,
            parent: str | Context = BASE_SETTINGS_ID
    ):
        return self.add_settings(
            display_name=display_name,
            settings_data_key=settings_data_key,
            settings_data_default=settings_data_default,
            short_display_dict=Settings.BOOL_DISPLAY_DICT,
            parent=parent,
        )

    def bool_settings_template(
            self,
            id_: str,
            template_str_answer: str,
            template_str_menu: str,
            display_name: str = None,
            settings_data_key: str = None,
            settings_data_default: bool = False,
            parent: str | Context = BASE_SETTINGS_ID,
    ):
        settings_data_key = settings_data_key or id_

        async def wrap(ctx: Settings.Context[bool]):
            if ctx.result:
                ctx.data = ctx.result == 'on'
                return await ctx.query_answer(
                    template_str_answer.format(
                        "enabled ✅" if ctx.data else "disabled ❌"
                    )
                )

            await ctx.update_message_with_boolean_btn(
                template_str_menu.format(
                    (
                        "✅ <b>Enabled</b>"
                        if ctx.data
                        else "❌ <b>Disabled</b>"
                    )
                )
            )

        wrap.__name__ = id_
        return self.add_bool_settings(
            display_name=display_name,
            settings_data_key=settings_data_key,
            settings_data_default=settings_data_default,
            parent=parent,
        )(wrap)

    async def _base_settings(
            self,
            update: Update,
            context: CallbackContext
    ):
        print("base")
        func = (
            update.callback_query.message.edit_text
            if update.callback_query and update.callback_query.message
            else update.message.reply_text
        )

        if update.callback_query:
            await update.callback_query.answer()

        settings_data = context.chat_data
        if update.effective_chat.type == ChatType.PRIVATE:
            settings_data = context.user_data

        buttons: list[InlineKeyboardButton] = []
        for id_, sub in self._settings.items():
            if id_ == BASE_SETTINGS_ID or not sub.display_in_chat:
                continue

            current_data = settings_data.get(
                sub.settings_data_key,
                sub.settings_data_default
            )
            sdd = sub.short_display_dict

            display_current_data = (
                sdd(current_data)
                if callable(sdd)
                else sdd.get(current_data)
            )

            buttons.append(
                InlineKeyboardButton(
                    (
                        f"{sub.display_name}: {display_current_data}"
                        if display_current_data
                        else sub.display_name
                    ),
                    callback_data=id_,
                )
            )

        return await func(
            self.settings_title,
            reply_markup=InlineKeyboardMarkup([[b] for b in buttons])
        )

    async def callback(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE
    ):
        data, *_ = update.callback_query.data.strip().lower().split('=', 1)
        func = self._settings.get(data)
        if callable(func):
            return await func(update, context)
        return await update.callback_query.answer('Not implemented yet')

    def command_handler(self, command: str = BASE_SETTINGS_ID):
        print(self._settings)
        return CommandHandler(command, self._base_settings)

    def callback_handler(self):
        return CallbackQueryHandler(
            self.callback,
            pattern=f"^{BASE_SETTINGS_ID}"
        )
