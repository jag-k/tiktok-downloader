from typing import Any, TypeVar

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import Application, ExtBot
from telegram.ext import CallbackContext as CallbackContextBase

from app.constants import DEFAULT_LOCALE, Keys

_SET_DEFAULT = TypeVar("_SET_DEFAULT", bound=Any)


class ContextSettings:
    DEFAULTS: dict[Keys, str | bool] = {}

    def __init__(self, ctx: "CallbackContext"):
        self.ctx = ctx

    @property
    def _data(self) -> dict:
        # noinspection PyProtectedMember
        if self.ctx._chat_type == ChatType.PRIVATE:
            return self.ctx.user_data
        return self.ctx.chat_data

    def get(self, key: Keys, default: Any = None) -> Any:
        if default is None:
            default = self.DEFAULTS.get(key, None)

        return self._data.get(key.value, default)

    def set(self, key: Keys, value: Any) -> None:
        self._data[key.value] = value

    def setdefault(self, key: Keys, value: _SET_DEFAULT) -> _SET_DEFAULT:
        return self._data.setdefault(key.value, value)

    def __getitem__(self, key: Keys) -> Any:
        return self.get(key)

    def __setitem__(self, key: Keys, value: Any) -> None:
        self.set(key, value)

    def __str__(self):
        return str(self._data)

    def is_history_enabled(self, update: Update) -> bool:
        from app.settings.user_settings import HistoryTypes

        ht: HistoryTypes = self[Keys.HISTORY]
        match ht:
            case HistoryTypes.NONE:
                return False
            case HistoryTypes.ALL:
                return True
            case HistoryTypes.PRIVATE:
                return update.effective_chat.type == ChatType.PRIVATE
            case HistoryTypes.GROUPS:
                return update.effective_chat.type in (
                    ChatType.GROUP,
                    ChatType.SUPERGROUP,
                    ChatType.PRIVATE,
                )
            case HistoryTypes.INLINE:
                return update.inline_query is not None
        return False


class CallbackContext(CallbackContextBase[ExtBot, dict, dict, dict]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__chat_type: ChatType | None = None
        self._user_lang: str | None = None
        self.settings: ContextSettings = ContextSettings(self)

    @property
    def history(self) -> list:
        return self.user_data.setdefault(Keys.HISTORY.value, [])

    @history.setter
    def history(self, value: list):
        self.user_data[Keys.HISTORY.value] = value

    @property
    def temp_history(self):
        return self.user_data.setdefault("tmp_history", {})

    @temp_history.setter
    def temp_history(self, value: dict):
        self.user_data["tmp_history"] = value

    @property
    def _chat_type(self) -> ChatType | None:
        return self.__chat_type

    @_chat_type.setter
    def _chat_type(self, value: ChatType) -> None:
        self.__chat_type = value

    @property
    def user_lang(self) -> str:
        return self.settings.get(
            Keys.LANGUAGE, self._user_lang or DEFAULT_LOCALE
        )

    @classmethod
    def from_update(
        cls: type["CallbackContext"],
        update: Update,
        application: Application,
    ) -> "CallbackContext":
        obj: CallbackContext = super().from_update(update, application)
        obj._chat_type = (
            update.effective_chat.type
            if update.effective_chat
            else ChatType.PRIVATE
        )
        if update.effective_user:
            obj._user_lang = update.effective_user.language_code
            obj.settings.setdefault(
                Keys.LANGUAGE, obj._user_lang or DEFAULT_LOCALE
            )
        return obj

    @property
    def media_cache(self) -> dict[str, dict]:
        return self.bot_data.setdefault("media_cache", {})

    @media_cache.setter
    def media_cache(self, value: dict[str, dict]):
        self.bot_data["media_cache"] = value

    @property
    def tg_video_cache(self) -> dict[str, dict]:
        return self.bot_data.setdefault("tg_video_cache", {})

    @tg_video_cache.setter
    def tg_video_cache(self, value: dict[str, dict]):
        self.bot_data["tg_video_cache"] = value
