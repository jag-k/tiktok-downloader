import gettext
from typing import Type, Any

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import CallbackContext as CallbackContextBase, ExtBot, \
    Application

from app.constants import LOCALE_PATH, DOMAIN, DEFAULT_LOCALE


class CallbackContext(CallbackContextBase[ExtBot, dict, dict, dict]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__chat_type: ChatType | None = None

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
        # self.update_lang()

    def update_lang(self):
        print(f"Start translate")
        lang = self.settings_get('language', DEFAULT_LOCALE)
        print(f"Start translate {lang}")
        t = gettext.translation(DOMAIN, LOCALE_PATH, languages=[lang])
        print(f"Installing translate {lang}")
        t.install([])
        print(f"Finish")

    @property
    def settings_data(self) -> dict:
        if self._chat_type != ChatType.PRIVATE:
            return self.chat_data
        return self.user_data

    def settings_get(self, key: str, default: Any = None) -> Any:
        first, second = (
            (self.chat_data, self.user_data)
            if self._chat_type != ChatType.PRIVATE
            else (self.user_data, self.chat_data)
        )
        return first.get(key, second.get(key, default))

    def settings_set(self, key: str, value: Any) -> None:
        self.settings_data[key] = value

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
        return ctx
