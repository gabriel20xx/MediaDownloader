import os
import time
from datetime import datetime
from bs4 import BeautifulSoup

from .utils.parser import create_parser
from .utils.config import read_configuration
from .utils.request import retry_request
from .utils.output import initialize_logs, output, Level

# Global config variables
file_name = "rarbg.yml"
base_urls = [
    "https://www2.rarbggo.to/",
    "https://rargb.to/",
    "https://www.rarbgproxy.to/",
    "https://www.rarbgo.to/",
    "https://www.proxyrarbg.to/",
]
use_index_page = True
use_search_queries = False
magnet_file = os.path.join(os.getcwd(), "Magnets.txt")
search_queries = []
delay = 5
user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
)

# Global variables
total_downloads = 0
debug_logger = None
download_logger = None


def parse_website(url, base_urls, magnet_file, user_agent, delay):
    """Parse listing/search pages and enqueue magnet links."""

    global debug_logger

    time.sleep(delay)
    response = retry_request(url, user_agent, debug_logger, 5, 0, base_urls)
    if response is None:
        message = f"Failed to retrieve the page: {url}"
        output(message, debug_logger, Level.ERROR)
        return False

    message = f"Parsing page: {response.url}"
    output(message, debug_logger, Level.INFO)
    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.select("tr.table2ta > td:nth-child(2) > a")
    message = f"Found {len(links)} links on the page."
    output(message, debug_logger, Level.INFO)
    if links:
        for link in links:
            time.sleep(delay)
            link_url = link["href"]
            response_followed = retry_request(
                link_url, user_agent, debug_logger, 5, 0, base_urls
            )

            if response_followed is None:
                message = f"Failed to retrieve the movie page: {link_url}"
                output(message, debug_logger, Level.WARNING)
                continue

            message = f"Parsing movie page: {response_followed.url}"
            output(message, debug_logger, Level.INFO)
            soup_followed = BeautifulSoup(response_followed.content, "html.parser")

            link_element = soup_followed.select_one("td.tlista a")
            magnet_link = link_element["href"] if link_element else None
            if magnet_link is None:
                message = f"No magnet link found on page {link_url}"
                output(message, debug_logger, Level.WARNING)

            title_element = soup_followed.select_one("td.block b h1.black")
            title = title_element.text.strip() if title_element else None
            if title is None:
                message = f"No title found on page {link_url}"
                output(message, debug_logger, Level.WARNING)

            if magnet_link and title:
                message = f"Magnet found for: {title}"
                output(message, debug_logger, Level.INFO)
                parse_magnet(
                    magnet_file,
                    magnet_link,
                    title,
                )
            else:
                message = "No magnet link and/or title found on the page."
                output(message, debug_logger, Level.ERROR)
        return True

    message = "No links found on page, exiting script."
    output(message, debug_logger, Level.WARNING)
    return False


def parse_magnet(magnet_file, magnet_link, title):
    """Persist a magnet link if it is new."""

    global debug_logger
    global download_logger
    global total_downloads

    if not os.path.exists(magnet_file):
        with open(magnet_file, "w") as file:
            file.write(f"{magnet_link}\n")

        message = f"Created a new file and added magnet link for this torrent: {title}"
        output(message, debug_logger, Level.INFO)
        total_downloads += 1
        return

    with open(magnet_file, "r") as file:
        existing_links = file.readlines()

    if magnet_link + "\n" not in existing_links:
        with open(magnet_file, "a") as file:
            file.write(f"{magnet_link}\n")
        message = f"Added magnet link: {title}"
        output(message, download_logger, Level.SUCCESS)
        total_downloads += 1
    else:
        message = f"Magnet link already exists in the file for this torrent: {title}"
        output(message, debug_logger, Level.INFO)


def rarbg_downloader():
    # Start timer
    start_time = datetime.now()

    # Import global config values
    global file_name
    global base_urls
    global use_index_page
    global use_search_queries
    global magnet_file
    global delay
    global user_agent

    # Import global variables
    global debug_logger
    global download_logger

    # Loading config
    config = read_configuration(file_name)
    if "logs_directory" in config:
        logs_directory = config["logs_directory"]
    if "prefix" in config:
        prefix = config["prefix"]
    if "use_index_page" in config:
        use_index_page = config["use_index_page"]
    if "use_search_queries" in config:
        use_search_queries = config["use_search_queries"]
    if "magnet_file" in config:
        magnet_file = config["magnet_file"]
    if use_search_queries and "search_queries" in config:
        search_queries = config["search_queries"]
    if "user_agent" in config:
        user_agent = config["user_agent"]
    if "delay" in config:
        delay = config["delay"]

    # Loading Parser
    if 1 == 2:
        create_parser()

    # Create and configure Loggers
    debug_logger, download_logger = initialize_logs(logs_directory, prefix)
    message = "Script started."
    output(message, debug_logger, Level.INFO)

    # Query index page
    if use_index_page:
        # Set page_number to 1
        page_number = 1
        while True:
            # Generate url
            url = f"xxx/{page_number}/"

            # Call the parse_website function
            result = parse_website(
                url,
                base_urls,
                magnet_file,
                user_agent,
                delay,
            )

            # Increase page_number if result succeeded or exit loop if False
            if result is True:
                page_number += 1
            else:
                break

    # Query search queries
    if use_search_queries:
        for query in search_queries:
            # Set page_number to 1
            page_number = 1
            while True:
                # Generate url
                url = f"search/{page_number}/?search={query}&category=xxx"

                # Call the parse_website function
                result = parse_website(
                    url,
                    base_urls,
                    magnet_file,
                    user_agent,
                    delay,
                )

                # Increase page_number if result succeeded or exit loop if False
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
    rarbg_downloader()
