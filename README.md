# MediaDownloader

MediaDownloader is now a Node.js application with a modern web UI, PostgreSQL backing store, and cron-based scheduling.

## Features

- Web UI for creating and managing download jobs
- Cron scheduling with immediate run support
- PostgreSQL persistence for jobs and logs
- Docker support

## Requirements

- Node.js 20+
- PostgreSQL

## Environment

Set the database connection string via `POSTGRESQL_URL`.

Example: copy .env.example to .env and update values.

## Install & Run

1) Install dependencies

2) Start the server

The app serves the UI at http://localhost:3000 by default.

## API

- GET /api/jobs
- POST /api/jobs
- PUT /api/jobs/:id
- DELETE /api/jobs/:id
- POST /api/jobs/:id/run
- GET /api/jobs/:id/logs

## Docker

Build and run with a PostgreSQL container and pass POSTGRESQL_URL to the app container.

## Notes

Downloads are saved to a local downloads/ folder inside the app container or project root.
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
