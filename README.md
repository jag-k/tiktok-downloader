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

These constants using for getting path to files. You can see these paths in this document.

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

You can image this like these structure:

```markdown
Contacts:

- {type}: [{text}]({url})
```

Any of these fields can be internationalized.
For this you need to set `_{lang}` suffix in keys.
For example: `type_ru` or `text_en`.
By default, using `DEFAULT_LOCALE` env variable or suffix-less key.

## 🔊 Notification service

This service can send notifications about errors and other events to different services.

### Supported services

| Support | Service                               | Code Name       | Description                                 | Events type support         |
|---------|---------------------------------------|-----------------|---------------------------------------------|-----------------------------|
| ✅       | [Save to file](#module-file_reporter) | `file_reporter` | Saving data to JSON file                    | `REPORT`                    |
| ✅       | [Chanify](#module-chanify)            | `chanify`       | [Chanify.net](https://chanify.net)          | [Any](#all-supported-event) |
| ✅       | [Ntfy](#module-ntfy)                  | `ntfy`          | [ntfy.sh](https://ntyf.sh)                  | [Any](#all-supported-event) |
| ❌       | Pushsafer                             | `pushsafer`     | [pushsafer.com](https://www.pushsafer.com/) | [Any](#all-supported-event) |
| ❌       | Email                                 | `email`         | Email notification                          | [Any](#all-supported-event) |
| ❌       | Gotify                                | `gotify`        | [Gotify.net](https://gotify.net/)           | [Any](#all-supported-event) |
| ❌       | Pushover                              | `pushover`      | [Pushover.net](https://pushover.net/)       | [Any](#all-supported-event) |
| ❌       | PushBullet                            | `pushbullet`    | [PushBullet.com](https://pushbullet.com/)   | [Any](#all-supported-event) |
| ❌       | Telegram                              | `telegram`      | [Telegram.org](https://telegram.org)        | [Any](#all-supported-event) |
| ❌       | Discord                               | `discord`       | [Discord.com](https://discord.com/)         | [Any](#all-supported-event) |

- ✅ -- Full Supported now
- ❌ -- Not yet implemented

### All supported events

- [x] `REPORT` -- The user submits an error while parsing from inline
- [x] `EXCEPTION` -- Bot catch exception on top level
- [x] `START` -- Bot started
- [x] `STOP` -- Bot stopped
- [x] `SHUTDOWN` -- Bot shutdown

### Configurate

Set env `NOTIFY_PATH` with a path to config. Default path is `CONFIG_PATH/notify.json`

Example of `notify.json`:

```json5
{
  // This is optional, used for validation in your IDE
  "$schema": "https://jag-k.github.io/tiktok-downloader/schemas/notify.schema.json",
  "services": [
    {
      "service": "file_reporter"
    },
    {
      "service": "file_reporter",
      "config": {
        "file_path": "/path/to/reporter/file.json"
      }
    },
    {
      "service": "chanify",
      "types": [
        "report"
      ],
      "config": {
        "url": "https://api.chanify.net",
        "token": "123"
      }
    },
    {
      "service": "chanify",
      "types": [
        "exception"
      ],
      "config": {
        "url": "https://api.example.com",
        "token": "456"
      }
    }
  ]
}
```

You can validate your config with [JSON Schema](https://json-schema.org/).
[Link to schema](https://jag-k.github.io/tiktok-downloader/schemas/notify.schema.json)

<!--region:notify-->

#### Module `chanify`

A wrapper for [Chanify](https://chanify.net) Notifications

Config:

| Name    | Description        | Default value             | Required |
|---------|--------------------|---------------------------|----------|
| `token` | Chanify token      |                           | ✅ True   |
| `url`   | Chanify server url | `https://api.chanify.net` | ❌ False  |

#### Module `file_reporter`

Reporter that writes reports to a file.

Config:

| Name        | Description         | Default value  | Required |
|-------------|---------------------|----------------|----------|
| `file_path` | Path to report file | `$REPORT_PATH` | ❌ False  |

#### Module `ntfy`

A wrapper for [Ntfy](https://ntfy.sh) Notifications

Config:

| Name         | Description                       | Default value       | Required |
|--------------|-----------------------------------|---------------------|----------|
| `url`        | Ntfy server url                   | `https://ntfy.sh`   | ❌ False  |
| `topic`      | Ntfy topic                        | `tiktok-downloader` | ❌ False  |
| `token`      | Ntfy token                        | `None`              | ❌ False  |
| `token_type` | Ntfy token type (Bearer or Basic) | `Bearer`            | ❌ False  |
| `send_file`  | Send file with notification       | `False`             | ❌ False  |

<!--endregion:notify-->

## Development

This project use [Poetry](https://python-poetry.org/) for dependency management.

For database project use MongoDB. More about this you can read [here](#database).

### Install project

Python version: **3.11**
Poetry version: **1.4.1**

```bash
poetry install
pre-commit install
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

You can use this for updating I18n files, generate schemas and more.

<!--region:makefile-->

```bash
make compile_locale  # Extract strings from code to .POT file
make extract_locale  # Update .PO file for Russian language
make update_locale  # Extract strings and update .PO file for Russian language
make full_update_locale  # Compile .PO files to .MO files
make generate_notify_schema  # Generate schema for notify.json file
make generate_notify_md  # Generate markdown for notify.json file
make generate_makefile  # Generate Makefile
make generate_makefile_md  # Generate Makefile and update README.md
make full_update_readme  # Full update README.md
```

<!--endregion:makefile-->
