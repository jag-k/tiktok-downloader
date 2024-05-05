from enum import Enum

from app.constants import Keys
from app.utils import CURRENT_LANG
from app.utils.i18n import _

from .base import Settings

s = Settings()

LANGUAGES = {
    "us": "🇺🇸 English",
    "ru": "🇷🇺 Русский",
}

SHORT_LANGUAGES = {
    "us": "🇺🇸",
    "ru": "🇷🇺",
}


@s.add_settings(_("🌍 Change language"), Keys.LANGUAGE, "us", SHORT_LANGUAGES)
async def change_language(ctx: Settings.Context[str]) -> None:
    if ctx.result and (lang := ctx.result.strip().lower()) in LANGUAGES:
        ctx.data = lang
        ctx.update_context_var(CURRENT_LANG, lang)
        return await ctx.query_answer(_("Language changed to {}!").format(LANGUAGES[lang]))

    def check(language: str) -> str:
        if ctx.data == language:
            return " ✅"
        return ""

    await ctx.update_message(
        text=_("Choose language"),
        buttons=[
            ctx.btn(text=f"{lang_name}{check(lang_code)}", result=lang_code)
            for lang_code, lang_name in LANGUAGES.items()
        ],
    )


add_author_mention = s.bool_settings_template(
    id_=Keys.ADD_AUTHOR_MENTION,
    display_name=_("👤 Add author in media"),
    template_str_answer=_("Add author in media are {}!"),
    template_str_menu=_(
        "Add author in media (video/audio/images):" "\n\n{}\n\n" "Example: So funny video by <code>@username</code>"
    ),
    settings_data_default=False,
)

add_original_link = s.bool_settings_template(
    id_=Keys.ADD_ORIGINAL_LINK,
    display_name=_("🔗 Add original link in media"),
    template_str_answer=_("Add original link in media are {}!"),
    template_str_menu=_(
        "Add original link in media:" "\n\n{}\n\n" "<i>️📝 NOTE!</i> Twitter always add original link in media."
    ),
    settings_data_default=False,
)

tiktok_flag = s.bool_settings_template(
    id_=Keys.TIKTOK_FLAG,
    display_name=_("🏳️ Add flag to TikTok videos/images"),
    template_str_answer=_("Add flag to TikTok videos/images are {}!"),
    template_str_menu=_(
        "Adds the flag of the country from which the videos/images was " "uploaded (author's country):\n\n{}"
    ),
    settings_data_default=False,
)


class DescriptionTypes(str, Enum):
    FULL = "full"
    WITHOUT_HASHTAGS = "without_hashtags"
    NONE = "none"


DESCRIPTION_SHORT = {
    DescriptionTypes.FULL: _("📜 All"),
    DescriptionTypes.WITHOUT_HASHTAGS: _("👤 Hash-less"),
    DescriptionTypes.NONE: _("❌ None"),
}

DESCRIPTION_DISPLAY = {
    DescriptionTypes.FULL: _("📜 All"),
    DescriptionTypes.WITHOUT_HASHTAGS: _("👤 Without hashtags"),
    DescriptionTypes.NONE: _("❌ Without description"),
}


@s.add_settings(
    _("📃️ Add description to videos/images"),
    Keys.ADD_DESCRIPTION,
    DescriptionTypes.NONE.value,
    DESCRIPTION_SHORT,
)
async def add_description(ctx: Settings.Context[str]) -> None:
    if ctx.result:
        ctx.data = ctx.result
        return await ctx.query_answer(
            _("Adding description changed to {}!").format(DESCRIPTION_DISPLAY[DescriptionTypes(ctx.data)])
        )

    def check(d: str) -> str:
        if ctx.data == d:
            return " ✅"
        return ""

    await ctx.update_message(
        text=_(
            "Choose type of adding the descriptions from the original source "
            "to the videos/images:\n\n"
            "Current: <b>{}</b>"
        ).format(DESCRIPTION_DISPLAY[DescriptionTypes(ctx.data)]),
        buttons=[
            ctx.btn(
                text=f"{description_name}{check(description_type)}",
                result=description_type.value,
            )
            for description_type, description_name in DESCRIPTION_DISPLAY.items()
        ],
        columns=1,
    )


add_media_source = s.bool_settings_template(
    id_=Keys.ADD_MEDIA_SOURCE,
    display_name=_("📬 Add media source to videos/images"),
    template_str_answer=_("Add media source to videos/images are {}!"),
    template_str_menu=_(
        "Add the social network where the videos/images were taken from:"
        "\n\n{}\n\n"
        "Example: So funny video from TikTok"
    ),
    settings_data_default=False,
)


class HistoryTypes(str, Enum):
    ALL = "all"
    GROUPS = "groups"
    PRIVATE = "private"
    INLINE = "inline"
    NONE = "none"


HISTORY_SHORT = {
    HistoryTypes.ALL: _("📜 All"),
    HistoryTypes.GROUPS: _("👥 Groups"),
    HistoryTypes.PRIVATE: _("👤 Private"),
    HistoryTypes.INLINE: _("🔎 Inline"),
    HistoryTypes.NONE: _("❌ Not save"),
}

HISTORY_DISPLAY = {
    HistoryTypes.ALL: _("📜 All"),
    HistoryTypes.GROUPS: _("👥 Groups, where bot are added"),
    HistoryTypes.PRIVATE: _("👤 Private (in bot chat)"),
    HistoryTypes.INLINE: _("🔎 Inline queries"),
    HistoryTypes.NONE: _("❌ Not saving history"),
}


@s.add_settings(
    _("📝 Saving History"),
    Keys.HISTORY,
    HistoryTypes.NONE,
    HISTORY_SHORT,
    False,
)
async def saving_history(ctx: Settings.Context[str]) -> None:
    if ctx.result:
        ctx.data = ctx.result
        return await ctx.query_answer(
            _("History saving changed to {}!").format(HISTORY_DISPLAY[HistoryTypes[ctx.result]])
        )

    def check(history: str) -> str:
        if ctx.data == history:
            return " ✅"
        return ""

    await ctx.update_message(
        text=_(
            "Choose source to save in history. " "To see the history, use <i>Inline Query</i>.\n\n" "Current: <b>{}</b>"
        ).format(HISTORY_DISPLAY[HistoryTypes[ctx.data]]),
        buttons=[
            ctx.btn(text=f"{history_name}{check(history_type)}", result=history_type)
            for history_type, history_name in HISTORY_DISPLAY.items()
        ],
        columns=1,
    )
