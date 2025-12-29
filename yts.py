import os
import re
import time
import random
from datetime import datetime, timedelta
from urllib.parse import unquote
from bs4 import BeautifulSoup

from .utils.parser import create_parser
from .utils.config import read_configuration
from .utils.request import retry_request
from .utils.output import initialize_logs, output, Level

# Global (config) values
config_file_name = "yts.yml"
base_urls = ["https://yts.mx/", "https://yts.unblockit.download/"]
download_directory = os.path.join(os.getcwd(), "output", "Downloads")
alternative_download_directory = os.path.join(os.getcwd(), "output", "Alternative")
logs_directory = os.path.join(os.getcwd(), "logs")
resolutions = ["2160p", "1080p.x265", "1080p", "720p"]
languages = ["ENGLISH", "GERMAN", "SPANISH"]
release_years = ["2020-2029", "2010-2019", "2000-2009", "1990-1999", "1980-1989", "1970-1979", "1950-1969", "1900-1949"]
genres = ["action", "adventure", "animation", "biography", "comedy", "crime", "documentary", "drama", "family", "film-noir", "game-show", "history", "horror", "music", "musical", "mystery", "news", "reality-tv", "romance", "sci-fi", "sport", "talk-show", "thriller", "war", "western"]
random_resolutions = False
random_languages = False
random_release_years = False
random_genres = False
skipped_threshold = 20
max_duration = 720
delay = 0
user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
)

# Global variables
total_downloads = 0
skipped_since_last_success = 0
debug_logger = None
download_logger = None
random = random


def parse_website(
    base_urls,
    url,
    language,
    alternative_download_directory,
    download_directory,
    page_number,
    delay,
    user_agent,
):
    global debug_logger
    result = False
    response = retry_request(url, user_agent, debug_logger, 5, 0, base_urls)

    if response is not None:
        message = f"Parsing page {page_number}: {url}"
        output(message, debug_logger, Level.INFO)
        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.select("div.browse-movie-wrap > a:nth-child(1)")
        message = f"Found {len(links)} links on page {page_number}"
        output(message, debug_logger, Level.INFO)
        if len(links) != 0 and links is not None:
            for link in links:
                link_url = link["href"]
                response_followed = retry_request(
                    link_url, user_agent, debug_logger, 5, 0, base_urls
                )

                if response_followed is not None:
                    message = f"Parsing movie page: {link_url}"
                    output(message, debug_logger, Level.INFO)
                    soup_followed = BeautifulSoup(
                        response_followed.content, "html.parser"
                    )
                    download_links = soup_followed.select(
                        'div#movie-info > p > a[href*="download"]'
                    )

                    if download_links:
                        download_link = download_links[-1]

                        # Defensive: ensure we always get the href, even if download_link is a tag or a string
                        if hasattr(download_link, 'get') and download_link.get('href'):
                            download_url = download_link['href']
                        elif isinstance(download_link, str):
                            # Try to extract href from HTML string using regex (fallback)
                            import re
                            match = re.search(r'href=["\']([^"\']+)["\']', download_link)
                            if match:
                                download_url = match.group(1)
                            else:
                                download_url = download_link  # fallback, may still be wrong
                        else:
                            download_url = str(download_link)  # fallback

                        # Optionally, ensure it's a full URL (not a relative one)
                        if not download_url.startswith('http'):
                            # If it's a relative URL, prepend the base URL
                            download_url = base_urls[0].rstrip('/') + '/' + download_url.lstrip('/')

                        message = f"Found Download Link: {download_url}"
                        output(message, debug_logger, Level.INFO)
                        result = parse_download(
                            base_urls,
                            download_url,
                            language,
                            alternative_download_directory,
                            download_directory,
                            user_agent,
                        )
                        if result is False:
                            result = result
                    else:
                        message = "No matching download link found."
                        output(message, debug_logger, Level.WARNING)
                else:
                    message = "Failed to retrieve the movie page."
                    output(message, debug_logger, Level.WARNING)
                time.sleep(delay)
        else:
            message = "No links found on page."
            output(message, debug_logger, Level.WARNING)
    else:
        message = f"Failed to retrieve the page {url}"
        output(message, debug_logger, Level.ERROR)
    return result


def parse_download(
    base_urls,
    url,
    language,
    alternative_download_directory,
    download_directory,
    user_agent,
):
    global debug_logger
    global download_logger
    response = retry_request(url, user_agent, debug_logger, 5, 0, base_urls)

    if response is not None:
        content_disposition = response.headers.get("Content-Disposition", "").split(";")
        original_filename = None

        for part in content_disposition:
            if "filename" in part:
                original_filename = unquote(part.split("=")[1].strip('"'))
                break

        if not original_filename:
            message = "No Content-Disposition found, using basename."
            output(message, debug_logger, Level.INFO)
            original_filename = os.path.basename(base_urls[0] + url)

        resolution_pattern = r"\[(2160p|1080p|720p)\]"
        quality_pattern = r"\b(BluRay|WEBRip)\b"
        compression_pattern = r"\[(x265)\]"
        match = re.search(resolution_pattern, original_filename)

        if match:
            resolution = match.group(1)  # Get the resolution

            # Check for compression match
            if re.search(compression_pattern, original_filename):
                resolution += ".x265"  # Add .x265 if compression is found
        else:
            resolution = "None"

        message = f"File found: {original_filename}"
        output(message, debug_logger, Level.INFO)

        # Ensure lowercase for language for consistency
        language_path = language.capitalize()

        RESOLUTION_PRIORITY = {
            "2160p.x265": 6,
            "2160p": 5,
            "1080p.x265": 4,
            "1080p": 3,
            "720p.x265": 2,
            "720p": 1,
            "None": 0,
        }

        # Search for existing torrent files with different resolutions/qualities and remove them if necessary
        cleaned_filename = re.sub(r"\((\d{4})\).*", r"(\1)", original_filename)
        for dirpath, _, filenames in os.walk(
            os.path.join(alternative_download_directory, language_path)
        ):
            for filename in filenames:
                if cleaned_filename in filename:
                    match = re.search(resolution_pattern, filename)
                    if match:
                        old_resolution = match.group(1)
                        # Check for compression match
                        if re.search(compression_pattern, filename):
                            old_resolution += ".x265"
                        # Compare the priorities using the RESOLUTION_PRIORITY dictionary
                        if (
                            RESOLUTION_PRIORITY.get(old_resolution, 0)
                            > RESOLUTION_PRIORITY.get(resolution, 0)
                        ):
                            return False
                        elif (
                            RESOLUTION_PRIORITY.get(old_resolution, 0)
                            == RESOLUTION_PRIORITY.get(resolution, 0)
                        ):
                            match = re.search(quality_pattern, filename)
                            if match:
                                old_quality = match.group(1)
                                if old_quality == "BluRay":
                                    return False
                        os.remove(os.path.join(dirpath, filename))

        # Combine language and resolution paths
        alternative_download_path = os.path.join(
            alternative_download_directory, language_path, resolution
        )
        download_path = os.path.join(download_directory, language_path, resolution)

        # Create directories if they don't exist
        os.makedirs(alternative_download_path, exist_ok=True)
        os.makedirs(download_path, exist_ok=True)

        # Construct full file paths
        store_path = os.path.join(alternative_download_path, original_filename)
        download_path = os.path.join(download_path, original_filename)

        global skipped_since_last_success
        if os.path.exists(store_path):
            skipped_since_last_success += 1
            message = f"File: {original_filename} already exists on store path. \
                {skipped_since_last_success} skipped since last success. Skipping..."
            output(message, debug_logger, Level.SKIP)
        else:
            with open(download_path, "wb") as f:
                f.write(response.content)

            with open(store_path, "wb") as f:
                f.write(response.content)

            global total_downloads
            total_downloads += 1
            skipped_since_last_success = 0
            message = f"Downloaded file: {original_filename}"
            output(message, download_logger, Level.SUCCESS)
        return True
    else:
        message = "Failed to retrieve the download."
        output(message, debug_logger, Level.ERROR)
        return False


def yts_downloader():
    # Start timer
    start_time = datetime.now()

    # Import global config values
    global config_file_name
    global base_urls
    global download_directory
    global alternative_download_directory
    global logs_directory
    global prefix
    global resolution
    global languages
    global release_years
    global genres
    global random_resolutions
    global random_languages
    global random_release_years
    global random_genres
    global max_duration
    global delay
    global user_agent
    global skipped_threshold

    # Import global variables
    global debug_logger
    global download_logger
    global random

    # Loading config
    config = read_configuration(config_file_name)
    if "download_directory" in config:
        download_directory = config["download_directory"]
    if "alternative_download_directory" in config:
        alternative_download_directory = config["alternative_download_directory"]
    if "logs_directory" in config:
        logs_directory = config["logs_directory"]
    if "prefix" in config:
        prefix = config["prefix"]
    if "resolutions" in config:
        resolutions = config["resolutions"]  # 2160p, 1080p.x265, 1080p
    if "languages" in config:
        languages = config["languages"]  # GERMAN, ENGLISH, SPANISH
    if "release_years" in config:
        release_years = config["release_years"]
    if "genres" in config:
        genres = config["genres"]
    if "random_resolutions" in config:
        random_resolutions = config["random_resolutions"]
    if "random_languages" in config:
        random_languages = config["random_languages"]
    if "random_release_years" in config:
        random_release_years = config["random_release_years"]
    if "random_genres" in config:
        random_genres = config["random_genres"]
    if "max_duration" in config:
        max_duration = config["max_duration"]  # In minutes
    if "delay" in config:
        delay = config["delay"]  # In seconds
    if "user_agent" in config:
        user_agent = config["user_agent"]
    if "skipped_threshold" in config:
        skipped_threshold = config["skipped_threshold"]

    # Loading parser
    if 1 == 2:
        args = create_parser()
        if args.download_directory:
            download_directory = args.download_directory
        if args.alternative_download_directory:
            alternative_download_directory = args.alternative_download_directory
        if args.logs_directory:
            logs_directory = args.logs_directory
        if args.prefix:
            prefix = args.prefix
        if args.resolutions:
            resolutions = args.resolutions
        if args.languages:
            languages = args.languages
        if args.release_years:
            release_years = args.release_years
        if args.genres:
            genres = args.genres
        if args.random_resolutions:
            random_resolutions = args.random_resolutions
        if args.random_languages:
            random_languages = args.random_languages
        if args.random_release_years:
            random_release_years = args.random_release_years
        if args.random_genres:
            random_genres = args.random_genres
        if args.max_duration:
            max_duration = args.max_duration
        if args.delay:
            delay = args.delay
        if args.user_agent:
            user_agent = args.user_agent

    # Create and configure Loggers
    debug_logger, download_logger = initialize_logs(logs_directory, prefix)
    message = "Script started."
    output(message, debug_logger, Level.INFO)

    # Loading variables
    languages = [language.upper() for language in languages]
    language_mapping = {"ENGLISH": "en", "GERMAN": "de", "SPANISH": "es"}
    converted_max_duration = timedelta(minutes=max_duration)

    # Make lists to random order
    if random_resolutions:
        random.shuffle(resolutions)
    if random_languages:
        random.shuffle(languages)
    if random_release_years:
        random.shuffle(release_years)
    if random_genres:
        random.shuffle(genres)

    # Printing the values
    message = f"Download directory: {download_directory}"
    output(message, debug_logger, Level.INFO)
    message = f"Alternative download directory: {alternative_download_directory}"
    output(message, debug_logger, Level.INFO)
    message = f"Resolutions: {resolutions}"
    output(message, debug_logger, Level.INFO)
    message = f"Languages: {languages}"
    output(message, debug_logger, Level.INFO)
    message = f"Release Years: {release_years}"
    output(message, debug_logger, Level.INFO)
    message = f"Genres: {genres}"
    output(message, debug_logger, Level.INFO)
    message = f"Random resolutions: {random_resolutions}"
    output(message, debug_logger, Level.INFO)
    message = f"Random languages: {random_languages}"
    output(message, debug_logger, Level.INFO)
    message = f"Random release years: {random_release_years}"
    output(message, debug_logger, Level.INFO)
    message = f"Random genres: {random_genres}"
    output(message, debug_logger, Level.INFO)
    message = f"Max duration: {max_duration}"
    output(message, debug_logger, Level.INFO)
    message = f"Delay: {delay}"
    output(message, debug_logger, Level.INFO)
    message = f"User-Agent: {user_agent}"
    output(message, debug_logger, Level.INFO)
    message = f"Skipped threshold: {skipped_threshold}"
    output(message, debug_logger, Level.INFO)

    # Fetch pages
    for resolution in resolutions:
        for language in languages:
            language_short = language_mapping.get(language, "en")
            for release_year in release_years:
                if release_year == "all":
                    release_year = "0"
                for genre in genres:
                    # Set page_number to 1 for each language and resolution
                    page_number = 1

                    while True:
                        # Calculate if script running time is exceeding max duration
                        current_time = datetime.now()
                        elapsed_time = current_time - start_time
                        if elapsed_time > converted_max_duration:
                            message = f"Execution time exceeded {max_duration} minutes"
                            output(message, debug_logger, Level.WARNING)
                            exit()

                        # Generate url
                        url = f"browse-movies/0/{resolution}/{genre}/0/featured/{release_year}/{language_short}"
                        if page_number != 1:
                            url = url + f"?page={page_number}"

                        # Call the parse_website function
                        result = parse_website(
                            base_urls,
                            url,
                            language,
                            alternative_download_directory,
                            download_directory,
                            page_number,
                            delay,
                            user_agent,
                        )

                        # Increase page_number if result succeeded or go to next resolution if result is False
                        global skipped_since_last_success
                        if (
                            skipped_since_last_success >= skipped_threshold
                            and skipped_threshold != 0
                        ):
                            message = f"Reached the skipped threshhold of {skipped_threshold}."
                            output(message, debug_logger, Level.INFO)
                            break
                        if result is True:
                            page_number += 1
                        else:
                            break

    # Stop timer
    end_time = datetime.now()

    # Calculate script running time
    time_difference = str(end_time - start_time)
    message = f"Script finished. Duration: {time_difference}, Downloads: {str(total_downloads)}"
    output(message, debug_logger, Level.INFO)


if __name__ == "__main__":
    yts_downloader()
