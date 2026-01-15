import os
import sys
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

from .utils.parser import create_parser
from .utils.config import read_configuration
from .utils.output import initialize_logs, output, Level

# Global config variables
file_name = "bitmagnet.yml"
base_urls = ["http://192.168.2.45:3333"]
use_index_page = False
use_search_queries = True
magnet_file = os.path.join(os.getcwd(), "Magnets.txt")
max_pages = 0
search_queries = []
include_one = None
include_all = None
exclude_one = None
exclude_all = None

# Global variables
total_downloads = 0
debug_logger = None
download_logger = None


# Function to get magnet links from the page
def get_magnet_links(driver):
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Find all magnet links (adjust the selector based on the actual page)
    magnets = soup.find_all("a", href=True)
    magnet_links = [a["href"] for a in magnets if "magnet:" in a["href"]]

    return magnet_links


def await_page_load(driver, tag, seconds, old_content=None):
    # Wait until the page is fully loaded
    time.sleep(1)
    try:
        if old_content:
            WebDriverWait(driver, seconds).until(
                lambda driver: driver.find_element(By.TAG_NAME, tag).text != old_content
            )
        else:
            # Adjust the timeout and the condition as needed
            WebDriverWait(driver, seconds).until(
                EC.presence_of_element_located((By.TAG_NAME, tag))
            )
        body_text = driver.find_element(By.TAG_NAME, tag).text
        time.sleep(1)
        return body_text
    except Exception as e:
        message = f"Error occurred while waiting for the page to load: {e}"
        output(message, debug_logger, Level.ERROR)
        return False


def parse_website(
    base_urls,
    magnet_file,
    max_pages,
    search_queries=None,
):
    # Set up Chrome options to suppress logging
    chrome_options = Options()
    chrome_options.add_argument("--log-level=3")

    # chrome_options.add_argument('--headless')
    chrome_options.add_argument("window-size=1920,1080")

    # Set up Selenium with Chrome WebDriver
    sys.stderr = open(os.devnull, "w")
    base_dir = Path(__file__).resolve().parent

    if os.name == "nt":
        driver_candidates = [
            Path.cwd() / "dependencies" / "chromedriver" / "chromedriver.exe",
            base_dir / "dependencies" / "chromedriver" / "chromedriver.exe",
        ]
    elif os.name == "posix":
        driver_candidates = [
            Path.cwd() / "dependencies" / "chromedriver" / "chromedriver",
            base_dir / "dependencies" / "chromedriver" / "chromedriver",
        ]
    else:
        raise NotImplementedError

    driver_path = next((p for p in driver_candidates if p.exists()), driver_candidates[0])

    service = Service(str(driver_path))
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Normalize search queries so index pages can run without a query list.
    search_query_list = search_queries or [None]

    for search_query in search_query_list:
        message = f"Using search query: {search_query or 'index page'}"
        output(message, debug_logger, Level.INFO)

        # Open the webpage
        driver.get(base_urls[0])

        # Wait until the page is fully loaded
        body_text = await_page_load(driver, "tbody", 300)

        if search_query:
            # Find the search field and input the search query, then hit enter
            time.sleep(10)
            search_field = driver.find_element(
                By.CSS_SELECTOR, "input[placeholder='Search']"
            )
            search_field.send_keys(search_query)
            search_field.send_keys(Keys.RETURN)
            time.sleep(10)

        # Loop through pages to collect magnet links
        page_num = 1
        last_page = False
        all_magnet_links = []

        while page_num <= max_pages or max_pages == 0:
            message = f"Loading page {page_num}"
            output(message, debug_logger, Level.INFO)

            body_text = await_page_load(driver, "tbody", 300, body_text)

            message = f"Crawling page {page_num}"
            output(message, debug_logger, Level.INFO)

            # Get magnet links from the current page
            links = get_magnet_links(driver)
            all_magnet_links.extend(links)

            attempts = 0
            retry_attempts = 5
            wait_time = 5

            if not os.path.exists(magnet_file):
                with open(magnet_file, "w") as file:
                    message = "Created a new file"
                    output(message, debug_logger, Level.INFO)

            with open(magnet_file, "r") as file:
                existing_links = file.readlines()

            for link in links:
                matches_query = (
                    not search_query
                    or (search_query and search_query.lower() in link.lower())
                )
                if matches_query and "vr" in link.lower():
                    if link + "\n" not in existing_links:
                        with open(magnet_file, "a") as file:
                            file.write(f"{link}\n")
                        message = f"Added magnet link: {link}"
                        output(message, download_logger, Level.SUCCESS)
                        global total_downloads
                        total_downloads += 1
                    else:
                        message = (
                            f"Magnet link already exists in the file for this torrent: {link}"
                        )
                        output(message, debug_logger, Level.INFO)
                elif search_query:
                    message = f"Magnet link does not match search query: {link}"
                    output(message, debug_logger, Level.INFO)

            while attempts < retry_attempts:
                time.sleep(wait_time)
                next_button = driver.find_element(
                    By.CSS_SELECTOR, "button[mattooltip='Next page']"
                )
                if not next_button.is_enabled():
                    message = "Reached the last page, going to next query."
                    output(message, debug_logger, Level.INFO)
                    last_page = True
                    break
                next_button.click()
                if next_button:
                    break  # Success, so break the loop

            if last_page is True:
                break
            page_num += 1

    # Close the WebDriver after scraping
    driver.quit()
    return True


def bitmagnet_downloader():
    # Start timer
    start_time = datetime.now()

    # Import global config values
    global file_name
    global base_urls
    global use_index_page
    global use_search_queries
    global max_pages
    global magnet_file
    global include_one
    global include_all
    global exclude_one
    global exclude_all

    # Import global variables
    global debug_logger
    global download_logger

    # Defaults that can be overridden by config
    logs_directory = "./logs"
    prefix = "BITMAGNET"

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
    if "max_pages" in config:
        max_pages = config["max_pages"]
    if use_search_queries and "search_queries" in config:
        search_queries = config["search_queries"]
    if "include_one" in config:
        include_one = config["include_one"]
    if "include_all" in config:
        include_all = config["include_all"]
    if "exclude_one" in config:
        exclude_one = config["exclude_one"]
    if "exclude_all" in config:
        exclude_all = config["exclude_all"]

    # Loading Parser
    if 1 == 2:
        create_parser()

    # Create and configure Loggers
    debug_logger, download_logger = initialize_logs(logs_directory, prefix)
    message = "Script started."
    output(message, debug_logger, Level.INFO)

    # Get dependencies
    # user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
    # get_dependencies("chrome", user_agent, debug_logger)
    # get_dependencies("chromedriver", user_agent, debug_logger)

    if use_index_page:
        parse_website(
            base_urls,
            magnet_file,
            max_pages,
        )

    if use_search_queries:
        parse_website(
            base_urls,
            magnet_file,
            max_pages,
            search_queries,
        )

    # Stop timer
    end_time = datetime.now()

    # Calculate script running time
    time_difference = str(end_time - start_time)
    message = f"Script finished. Duration: {time_difference}, Downloads: {str(total_downloads)}"
    output(message, debug_logger, Level.INFO)


if __name__ == "__main__":
    bitmagnet_downloader()
