# MediaDownloader

> **A unified toolkit for downloading media content from various sources**

MediaDownloader is a comprehensive Python package that combines multiple specialized downloaders into a single, easy-to-use tool. Whether you need to scrape image galleries, download torrents, or archive video content, MediaDownloader provides a unified interface to handle it all.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Image Gallery Scraper](#image-gallery-scraper)
  - [YTS Torrent Downloader](#yts-torrent-downloader)
  - [RARBG Magnet Extractor](#rarbg-magnet-extractor)
  - [Adult Video Scraper](#adult-video-scraper)
  - [Bitmagnet Scraper](#bitmagnet-scraper)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Important Notes](#important-notes)

## Features

MediaDownloader provides five specialized tools, each designed for specific use cases:

### 🖼️ Image Gallery Scraper
- Automatically downloads entire image galleries from supported websites
- Configurable CSS selectors for flexibility across different sites
- Smart filename sanitization and duplicate detection
- Support for multiple image formats (JPG, PNG, GIF, WebP, etc.)
- Video content filtering with customizable skip phrases

### 🎬 YTS Torrent Downloader
- Search and download movie torrents from YTS
- Filter by resolution (2160p, 1080p, 720p, etc.)
- Filter by language and release year
- Genre-based filtering
- Random selection mode for discovering new content
- Configurable download duration limits

### 🧲 RARBG Magnet Extractor
- Extract magnet links from RARBG mirror sites
- Category-based filtering
- Customizable search parameters
- Automatic fallback to alternative URLs

### 🔞 Adult Video Scraper
- Download adult content from supported platforms
- yt-dlp integration for video downloading
- Configurable quality preferences
- Site-specific metadata extraction

### 🔍 Bitmagnet Scraper
- Interface with Bitmagnet torrent indexing systems
- Advanced search capabilities
- Metadata extraction and organization

## Prerequisites

Before installing MediaDownloader, ensure you have the following:

- **Python 3.7+** - The package requires Python 3.7 or higher
- **Chrome/Chromium Browser** - Required for Selenium-based scrapers
- **ffmpeg** (Optional) - Required for video processing with yt-dlp
- **Git** - For cloning the repository

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/gabriel20xx/MediaDownloader.git
cd MediaDownloader
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Browser Drivers (Recommended)

For Playwright-based scraping (optional but recommended):

```bash
python -m playwright install --with-deps chromium
```

For Selenium-based scraping, place ChromeDriver in:
- `dependencies/chromedriver/` in your working directory, or
- Adjust the path in your configuration files

### 4. Install Additional Tools (Optional)

For yt-dlp functionality:

```bash
# yt-dlp is included in requirements.txt
# Ensure ffmpeg is available on your PATH for video processing
```

## Configuration

Each tool uses YAML configuration files located in the `configs/` directory. You can either:

1. **Edit the packaged configs** in `configs/` directory
2. **Create custom configs** in your working directory (takes precedence)

### Available Configuration Files

- **`configs/images.yaml`** - Image gallery scraper settings
  - Base URL, download folder, CSS selectors
  - Image extensions, skip phrases, timeouts

- **`configs/yts.yml`** - YTS torrent downloader settings
  - Download directories, resolutions, languages
  - Release years, genres, filtering options

- **`configs/rarbg.yml`** - RARBG settings
  - Mirror URLs, categories, search parameters

- **`configs/porn.yml`** - Adult video scraper settings
  - Site configurations, quality preferences

- **`configs/bitmagnet.yml`** - Bitmagnet scraper settings
  - API endpoints, search filters

**Note:** Configuration files in your current working directory will override the packaged defaults.

## Usage

MediaDownloader uses a unified launcher to access all tools. The general syntax is:

```bash
python -m media_downloader <tool_name>
```

### Image Gallery Scraper

Download entire image galleries from configured websites:

```bash
python -m media_downloader images
```

**What it does:**
- Navigates to the gallery overview page
- Extracts links to individual galleries
- Downloads all images from each gallery
- Organizes files by gallery title
- Skips videos if configured

**Configuration:** Edit `configs/images.yaml` to customize:
- Target website URL
- Download location
- CSS selectors for your target site
- Image file extensions to download

### YTS Torrent Downloader

Search and download movie torrents from YTS:

```bash
python -m media_downloader yts
```

**What it does:**
- Searches YTS for movies matching your criteria
- Filters by resolution, language, year, and genre
- Downloads matching torrents or magnet links
- Logs all activities for review

**Configuration:** Edit `configs/yts.yml` to customize:
- Preferred resolutions (4K, 1080p, 720p)
- Languages (English, German, Spanish, etc.)
- Release year ranges
- Favorite genres

### RARBG Magnet Extractor

Extract magnet links from RARBG:

```bash
python -m media_downloader rarbg
```

**What it does:**
- Searches RARBG mirror sites
- Extracts magnet links for torrents
- Saves links for use with torrent clients
- Handles site blocks with alternative URLs

**Configuration:** Edit `configs/rarbg.yml`

### Adult Video Scraper

Download adult content from supported platforms:

```bash
python -m media_downloader porn
```

**What it does:**
- Scrapes adult content websites
- Uses yt-dlp for video downloading
- Extracts metadata and thumbnails
- Organizes downloads by performer/title

**Configuration:** Edit `configs/porn.yml`

### Bitmagnet Scraper

Interface with Bitmagnet torrent indexing:

```bash
python -m media_downloader bitmagnet
```

**What it does:**
- Queries Bitmagnet torrent databases
- Extracts detailed torrent metadata
- Provides advanced search capabilities

**Configuration:** Edit `configs/bitmagnet.yml`

## Project Structure

```
MediaDownloader/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── __init__.py                 # Package initialization
├── __main__.py                 # Unified launcher entry point
├── images.py                   # Image gallery scraper module
├── yts.py                      # YTS torrent downloader module
├── rarbg.py                    # RARBG magnet extractor module
├── porn.py                     # Adult video scraper module
├── bitmagnet.py                # Bitmagnet scraper module
├── configs/                    # Configuration files
│   ├── images.yaml             # Image scraper config
│   ├── yts.yml                 # YTS downloader config
│   ├── rarbg.yml               # RARBG extractor config
│   ├── porn.yml                # Adult scraper config
│   └── bitmagnet.yml           # Bitmagnet scraper config
└── utils/                      # Shared utilities
    ├── config.py               # Configuration parser
    ├── dependencies.py         # Dependency management
    ├── generate_url.py         # URL generation helpers
    ├── output.py               # Logging utilities
    ├── parser.py               # HTML parsing utilities
    ├── request.py              # HTTP request helpers
    └── websites.json           # Site metadata database
```

## Troubleshooting

### Common Issues

**1. ChromeDriver not found**
```
Solution: Download ChromeDriver from https://chromedriver.chromium.org/
Place it in: dependencies/chromedriver/ or update config paths
```

**2. Playwright browser not installed**
```
Solution: Run: python -m playwright install --with-deps chromium
```

**3. Module not found errors**
```
Solution: Ensure you're in the correct directory and dependencies are installed:
pip install -r requirements.txt
```

**4. Rate limiting / Connection errors**
```
Solution: 
- Increase delay values in configuration files
- Consider using a VPN or proxy
- Check if the target site is accessible
```

**5. Downloads not working**
```
Solution:
- Verify download directory exists and is writable
- Check configuration file syntax (YAML formatting)
- Review logs in the logs/ directory for detailed error messages
```

**6. yt-dlp video download fails**
```
Solution:
- Ensure ffmpeg is installed and on your PATH
- Update yt-dlp: pip install --upgrade yt-dlp
- Check if the video URL is still valid
```

### Debug Mode

Each tool generates detailed logs in the `logs/` directory. Check these logs for:
- Request/response details
- Error stack traces
- Download progress
- Configuration issues

## Important Notes

### Legal and Ethical Considerations

⚠️ **Important:** This tool is provided for educational and personal use only. Users are responsible for:
- Complying with all applicable laws and regulations
- Respecting copyright and intellectual property rights
- Following the terms of service of websites being accessed
- Obtaining necessary permissions for content download

### Best Practices

- **Rate Limiting:** Adjust delays in configuration files to avoid overwhelming servers
- **VPN/Proxy:** Consider using when accessing geo-restricted content or to avoid IP bans
- **Storage:** Ensure adequate disk space for downloads
- **Updates:** Keep dependencies updated for security and compatibility
- **Backups:** Configuration files should be backed up before major changes

### Browser Requirements

- **Selenium:** Requires Chrome/Chromium browser and matching ChromeDriver version
- **Playwright:** Automatically manages browser binaries after installation
- Some sites may detect automated browsing; results may vary

### Default Behavior

- Logs are written to `logs/` directory (relative to working directory)
- Downloads default to `output/` directory (can be configured)
- Configuration lookup: Current directory first, then packaged configs
- Each tool runs independently and doesn't interfere with others

---

**Need help?** Open an issue on GitHub: https://github.com/gabriel20xx/MediaDownloader/issues
