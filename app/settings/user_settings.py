from app.settings.base import Settings

s = Settings()

LANGUAGES = {
    'us': '🇺🇸 English',
    'ru': '🇷🇺 Русский',
}

SHORT_LANGUAGES = {
    'us': '🇺🇸',
    'ru': '🇷🇺',
}


# @s.add_settings(_('🇪🇺 Change language'), 'language', 'us', SHORT_LANGUAGES)
# async def change_language(ctx: Settings.Context[str]):
#     if ctx.result and (lang := ctx.result.strip().lower()) in LANGUAGES:
#         ctx.data = lang
#         return await ctx.query_answer(
#             f'Language changed to {LANGUAGES[lang]}!'
#         )
#
#     def check(lang: str):
#         if ctx.data == lang:
#             return ' ✅'
#         return ''
#
#     await ctx.update_message(
#         text='Choose language',
#         buttons=[
#             ctx.btn(text=f'{lang_name}{check(lang_code)}', result=lang_code)
#             for lang_code, lang_name in LANGUAGES.items()
#         ]
#     )


add_author_mention = s.bool_settings_template(
    id_='add_author_mention',
    display_name='👤 Add author in media',
    template_str_answer='Add author in media are {}!',
    template_str_menu=(
        'Add author in media (video/audio/images):'
        '\n\n{}\n\n'
        'Example: So funny video by <code>@username</code> from TikTok'
    ),
    settings_data_key='add_author',
)

add_original_link = s.bool_settings_template(
    id_='add_original_link',
    display_name='🔗 Add original link in media',
    template_str_answer='Add original link in media are {}!',
    template_str_menu=(
        'Add original link in media:'
        '\n\n{}\n\n'
        '<i>️📝 NOTE!</i> Twitter always add original link in media.'
    ),
    settings_data_key='add_link',
)

tiktok_flag = s.bool_settings_template(
    id_='tiktok_flag',
    display_name='🏳️ Add flag to TikTok videos/images',
    template_str_answer='Add flag to TikTok videos/images are {}!',
    template_str_menu=(
        "Adds the flag of the country from which the videos/images was "
        "uploaded (author's country):\n\n{}"
    ),
)

HISTORY_SHORT = {
    'all': '📜 All',
    'groups': '👥 Groups',
    'private': '👤 Private',
    'inline': '🔎 Inline',
    'none': '❌ Not save',
}

HISTORY_DISPLAY = {
    'all': '📜 All',
    'groups': '👥 Groups, where bot are added',
    'private': '👤 Private (in bot chat)',
    'inline': "🔎 Inline queries (saves even if you didn't send the video)",
    'none': '❌ Not saving history',
}


@s.add_settings('📝 Saving History', 'history', 'all', HISTORY_SHORT, False)
async def saving_history(ctx: Settings.Context[dict]):
    if ctx.result:
        ctx.data = ctx.result
        return await ctx.query_answer(
            f'History saving changed to {HISTORY_DISPLAY[ctx.result]}!'
        )

    def check(history: str):
        if ctx.data == history:
            return ' ✅'
        return ''

    await ctx.update_message(
        text='Choose source to save in history. '
             'To see the history, use <i>Inline Query</i>.\n\n'
             f'Current: <b>{HISTORY_DISPLAY[ctx.data]}</b>',
        buttons=[
            ctx.btn(
                text=f"{history_name}{check(history_type)}",
                result=history_type
            )
            for history_type, history_name in HISTORY_DISPLAY.items()
        ],
        columns=1,
    )
