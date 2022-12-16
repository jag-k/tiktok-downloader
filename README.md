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
- [x] YouTube  (only "short" videos, Telegram doesn't support big files from bots)
- [x] Reddit
  - [x] Video without audio
  - [ ] Video with audio
- [x] Twitter
  - [x] Video
  - [ ] Images
- [ ] Instagram

## Development

### I18n

```bash
python -m cli extract  # Extract strings from code to .POT file
python -m cli update -l ru  #  Update .PO file for Russian language
python -m cli full_update -l ru  #  Extract strings and update .PO file for Russian language
python -m cli compile  # Compile .PO files to .MO files
```
