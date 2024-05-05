# Video downloader bot

[![Build and deploy Python app](https://github.com/jag-k/tiktok-downloader/actions/workflows/deploy.yml/badge.svg)](https://github.com/jag-k/tiktok-downloader/actions/workflows/deploy.yml)

Telegram bot for downloading videos from social networks.

## Translation

![POEditor ru lang](https://img.shields.io/poeditor/progress/580945/ru?token=d1b892d4d62ccf68a483db6de40a1cac)

## Support services

- [x] TikTok
  - [x] Video
  - [ ] Music from video
  - [ ] Images
- [x] YouTube
  - [x] Shorts
  - [x] Videos[^1]
- [x] Reddit
  - [x] Video without audio
  - [ ] Video with audio
- [x] Twitter
  - [x] Video
  - [ ] Images
- [x] Instagram
  - [x] Reels/video
  - [ ] Photo
  - [ ] Photo carousel
- [ ] Pinterest
  - [ ] Video
  - [ ] Images
- [ ] VK
  - [ ] Video
  - [ ] Images
  - [ ] Stories
  - [ ] Clips
- [ ] Vimeo
  - [ ] Video
  - [ ] Images
- [ ] Facebook
  - [ ] Video
  - [ ] Images

[^1]: Some videos can't be sent. Telegram have file limit (20 MB) for bots.

## How to use?

### Env variables

| Name           | Description                                                                            | Default value               | Required |
|----------------|----------------------------------------------------------------------------------------|-----------------------------|----------|
| TG_TOKEN       | Telegram token for bot (you can get this in [@BotFather](https://t.me/BotFather))      |                             | ✅ True   |
| MONGO_URL      | Url like `mongodb://user:password@localhost:27017/video-downloader` for using MongoDB. |                             | ✅ True   |
| MONGO_DB       | Name of MongoDB db like `video-downloader`                                             |                             | ✅ True   |
| BASE_PATH      | Path to project                                                                        | `PROJECT_PATH`              | ❌ False  |
| DEFAULT_LOCALE | Default bot locale. Now support only `en` and `ru`                                     | `en`                        | ❌ False  |
| LOCALE_DOMAIN  | Domain of locale (need for i18n module)                                                | `message`                   | ❌ False  |
| TZ             | Timezone. Using for log                                                                | `Europe/Moscow`             | ❌ False  |
| CONTACTS_PATH  | Path to json file for contacts. [More info](#contact-info)                             | `CONFIG_PATH/contacts.json` | ❌ False  |
| NOTIFY_PATH    | Default path for Notify module. [More info](#notification-service)                     | `CONFIG_PATH/notify.json`   | ❌ False  |
| REPORT_PATH    | Default path for `file_reporter`. [More info](#module-file_reporter)                   | `CONFIG_PATH/report.json`   | ❌ False  |

### Constant Path

These are constants used for getting a path to files. You can see these paths in this document.

| Name         | Description               | Value                            |
|--------------|---------------------------|----------------------------------|
| PROJECT_PATH | Real path to project      | Project path (can't be override) |
| CONFIG_PATH  | Path to config folder     | `$BASE_PATH/config`              |
| DATA_PATH    | Path to data folder       | `$BASE_PATH/data`                |
| LOG_PATH     | Path to log files         | `DATA_PATH/log`                  |
| LOCALE_PATH  | Path to localization data | `PROJECT_PATH/locales`           |

### Contact info

This is .json file like this:

```json
[
  {
    "type": "Author",
    "type_ru": "Автор",
    "text": "Jag_k",
    "url": "https://github.com/jag-k"
  },
  {
    "type": "Project GitHub Repo",
    "type_ru": "GitHub репозиторий проекта",
    "text": "@jag-k/tiktok-downloader",
    "url": "https://github.com/jag-k/tiktok-downloader"
  }
]
```

This file will be used in `/help` command.

You can image this like these structures:

```markdown
Contacts:

- {type}: [{text}]({url})
```

Any of these fields can be internationalised.
For this you need to set `_{lang}` suffix in keys.
For example: `type_ru` or `text_en`.
By default, using `DEFAULT_LOCALE` env variable or suffix-less key.

## Development

This project uses [Poetry](https://python-poetry.org/) for dependency management.

For database project use MongoDB. More about this you can read [here](#database).

### Install project

Python version: **3.12**
Poetry version: **1.8.2**

```bash
poetry install
pre-commit install
pre-commit install-hooks
```

### Database

You can run [docker-compose.yml](/docker-compose.yml) with MongoDB for development.

Example of `CONFIG_PATH/init-mongo.js` file:

```js
db.createUser(
  {
    user: "user",
    pwd: "password",
    roles: [
      {
        role: "readWrite",
        db: "video-downloader"
      }
    ]
  }
)
```

Example of `.env` file:

```dotenv
MONGO_URI=mongodb://user@password:localhost:27017/tiktok-downloader
MONGO_DB=tiktok-downloader
```

### Run project

```bash
poetry run python main.py
```

### Makefile commands

You can use this for updating I18n files, generate schemas, and more.

<!--region:makefile-->

```bash
make compile_locale  # Extract strings from code to .POT file
make extract_locale  # Update .PO file for Russian language
make update_locale  # Extract strings and update .PO file for Russian language
make full_update_locale  # Compile .PO files to .MO files
make generate_makefile  # Generate Makefile
make generate_makefile_md  # Generate Makefile and update README.md
make full_update_readme  # Full update README.md
```

<!--endregion:makefile-->
