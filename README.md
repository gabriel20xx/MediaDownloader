# MediaDownloader

MediaDownloader combines the image gallery scraper and the torrent/adult video downloaders into a single package. Use the launcher to run individual tools without juggling separate repositories.

## Project layout
- [media_downloader/images.py](media_downloader/images.py) – gallery scraper
- [media_downloader/bitmagnet.py](media_downloader/bitmagnet.py), [media_downloader/yts.py](media_downloader/yts.py), [media_downloader/rarbg.py](media_downloader/rarbg.py), [media_downloader/porn.py](media_downloader/porn.py) – torrent/adult downloaders
- [media_downloader/configs](media_downloader/configs) – packaged example configs (images.yaml, yts.yml, rarbg.yml, porn.yml, bitmagnet.yml)
- [media_downloader/utils](media_downloader/utils) – shared helpers and site metadata ([websites.json](media_downloader/utils/websites.json))

## Setup
```bash
pip install -r requirements.txt
# Optional but recommended for playwright fallback
python -m playwright install --with-deps chromium
```
For yt-dlp flows, ensure `yt-dlp` and `ffmpeg` binaries are on PATH (the downloader can grab yt-dlp automatically).

## Configuration
- Images scraper: edit [media_downloader/configs/images.yaml](media_downloader/configs/images.yaml).
- Torrent/adult tools: edit the YAML files in [media_downloader/configs](media_downloader/configs) (yts.yml, rarbg.yml, porn.yml, bitmagnet.yml). Config lookup checks the current working directory first, then the packaged configs.

## Running tools
Use the unified launcher:
```bash
python -m media_downloader images      # gallery scraper
python -m media_downloader yts         # YTS torrent downloader
python -m media_downloader rarbg       # RARBG magnet extractor
python -m media_downloader porn        # adult video scraper/downloader
python -m media_downloader bitmagnet   # Bitmagnet scraper
```
Each tool writes logs and downloads according to its config. Default paths are relative to your current working directory.

## Notes
- Selenium-based scripts expect Chrome/Chromedriver. Place the driver under `dependencies/chromedriver/` in your working directory (or alongside the package) or adjust paths in configs.
- Some sites block scraping; consider VPN/proxy and adjust delays if rate-limited.
- Respect site terms and local laws when downloading content.
