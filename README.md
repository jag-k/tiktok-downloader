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
  - [x] Reels
  - [ ] Photo
  - [ ] Photo carousel

[^1]: Some videos can't be sent. Telegram have file limit (20 MB) for bots.

## 🔊 Notification service

### Supported services

| Support | Service      | Code Name       | Description                               | Events catching now   |
|---------|--------------|-----------------|-------------------------------------------|-----------------------|
| ✅       | Save to file | `file_reporter` | Saving data to JSON file                  | `REPORT`              |
| ✅       | Chanify      | `chanify`       | [Chanify.net](https://chanify.net)        | `REPORT`, `EXCEPTION` |
| ❌       | Email        | `email`         | Email notification                        |                       |
| ❌       | PushBullet   | `pushbullet`    | [PushBullet.com](https://pushbullet.com/) |                       |


### Supported event

- [x] `REPORT` -- The user submits an error while parsing from inline
- [x] `EXCEPTION` -- Bbot catch exception on top level
- [ ] `START` -- Bot started
- [ ] `STOP` -- Bot stopped

### How to use?

Set env `NOTIFY_PATH` with path to config. Default: `CONFIG_PATH/notify.json`

Example of `notify.json`:

```json
[
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
    "types": ["report"],
    "config": {
      "url": "https://api.chanify.net",
      "token": "123"
    }
  },
  {
    "service": "chanify",
    "types": ["exeption"],
    "config": {
      "url": "https://api.example.com",
      "token": "456"
    }
  }
]

```

## Development

### Install project

Poetry version: **1.4.1**

```bash
poetry install
pre-commit install
```

### I18n

```bash
make extract  # Extract strings from code to .POT file
make update  # Update .PO file for Russian language
make full_update  # Extract strings and update .PO file for Russian language
make compile  # Compile .PO files to .MO files
```
