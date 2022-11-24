from typing import Type, Any

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import CallbackContext as CallbackContextBase, ExtBot, \
    Application

from app.constants import DEFAULT_LOCALE


class CallbackContext(CallbackContextBase[ExtBot, dict, dict, dict]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__chat_type: ChatType | None = None
        self._user_lang: str | None = None

    @property
    def history(self):
        return self.user_data.setdefault('history', [])

    @history.setter
    def history(self, value: list):
        self.user_data['history'] = value

    @property
    def _chat_type(self) -> ChatType | None:
        return self.__chat_type

    @_chat_type.setter
    def _chat_type(self, value: ChatType) -> None:
        self.__chat_type = value

    @property
    def settings_data(self) -> dict:
        if self._chat_type == ChatType.PRIVATE:
            return self.user_data
        return self.chat_data

    def settings_get(self, key: str, default: Any = None) -> Any:
        ud = self.user_data or {}
        cd = self.chat_data or {}

        first, second = (
            (ud, cd)
            if self._chat_type == ChatType.PRIVATE
            else (cd, ud)
        )
        return first.get(key, second.get(key, default))

    def settings_set(self, key: str, value: Any) -> None:
        self.settings_data[key] = value

    @property
    def user_lang(self) -> str:
        return self.settings_get(
            'language',
            self._user_lang or DEFAULT_LOCALE
        )

    @classmethod
    def from_update(
        cls: Type["CallbackContext"],
        update: Update,
        application: Application,
    ) -> "CallbackContext":
        ctx = super().from_update(update, application)
        ctx._chat_type = (
            update.effective_chat.type
            if update.effective_chat else
            ChatType.PRIVATE
        )
        if update.effective_user:
            ctx._user_lang = update.effective_user.language_code
        return ctx
