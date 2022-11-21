from app.settings.base import Settings
from app.utils.i18n import _

s = Settings()

LANGUAGES = {
    'us': '🇺🇸 English',
    'ru': '🇷🇺 Русский',
}

SHORT_LANGUAGES = {
    'us': '🇺🇸',
    'ru': '🇷🇺',
}


@s.add_settings(_('🇪🇺 Change language'), 'language', 'us', SHORT_LANGUAGES)
async def change_language(ctx: Settings.Context[str]):
    if ctx.result and (lang := ctx.result.strip().lower()) in LANGUAGES:
        ctx.data = lang
        return await ctx.query_answer(
            _('Language changed to {}!').format(LANGUAGES[lang])
        )

    def check(lang: str):
        if ctx.data == lang:
            return ' ✅'
        return ''

    await ctx.update_message(
        text=_('Choose language').s,
        buttons=[
            ctx.btn(text=f'{lang_name}{check(lang_code)}', result=lang_code)
            for lang_code, lang_name in LANGUAGES.items()
        ]
    )

"""
add_author_mention = s.bool_settings_template(
    id_='add_author_mention',
    display_name=_('👤 Add author in media'),
    template_str_answer=_('Add author in media are {}!'),
    template_str_menu=_(
        'Add author in media (video/audio/images):'
        '\n\n{}\n\n'
        'Example: So funny video by <code>@username</code> from TikTok'
    ),
    settings_data_key='add_author',
)

add_original_link = s.bool_settings_template(
    id_='add_original_link',
    display_name=_('🔗 Add original link in media'),
    template_str_answer=_('Add original link in media are {}!'),
    template_str_menu=_(
        'Add original link in media:'
        '\n\n{}\n\n'
        '<i>️📝 NOTE!</i> Twitter always add original link in media.'
    ),
    settings_data_key='add_link',
)

tiktok_flag = s.bool_settings_template(
    id_='tiktok_flag',
    display_name=_('🏳️ Add flag to TikTok videos/images'),
    template_str_answer=_('Add flag to TikTok videos/images are {}!'),
    template_str_menu=_(
        "Adds the flag of the country from which the videos/images was "
        "uploaded (author's country):\n\n{}"
    ),
)

HISTORY_SHORT = {
    'all': _('📜 All'),
    'groups': _('👥 Groups'),
    'private': _('👤 Private'),
    'inline': _('🔎 Inline'),
    'none': _('❌ Not save'),
}

HISTORY_DISPLAY = {
    'all': _('📜 All'),
    'groups': _('👥 Groups, where bot are added'),
    'private': _('👤 Private (in bot chat)'),
    'inline': _("🔎 Inline queries (saves even if you didn't send the video)"),
    'none': _('❌ Not saving history'),
}


@s.add_settings(_('📝 Saving History'), 'history', 'all', HISTORY_SHORT, False)
async def saving_history(ctx: Settings.Context[dict]):
    if ctx.result:
        ctx.data = ctx.result
        return await ctx.query_answer(
            _(
                'History saving changed to {}!'
            ).format(HISTORY_DISPLAY[ctx.result])
        )

    def check(history: str):
        if ctx.data == history:
            return ' ✅'
        return ''

    await ctx.update_message(
        text=_(
            'Choose source to save in history. '
            'To see the history, use <i>Inline Query</i>.\n\n'
            'Current: <b>{}</b>'
        ).format(HISTORY_DISPLAY[ctx.data]),
        buttons=[
            ctx.btn(
                text=f"{history_name}{check(history_type)}",
                result=history_type
            )
            for history_type, history_name in HISTORY_DISPLAY.items()
        ],
        columns=1,
    )
"""