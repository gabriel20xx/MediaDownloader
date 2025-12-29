import os
import re
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .utils.generate_url import get_category_number
from .utils.parser import create_parser
from .utils.config import read_configuration
from .utils.output import initialize_logs, output, Level
from .utils.request import retry_request
from .utils.dependencies import download_tool

# Global (config) values
config_file = "porn.yml"
WEBSITES_JSON_PATH = Path(__file__).resolve().parent / "utils" / "websites.json"

# Define default values for each variable
verbose = False
websites = []
search_queries = []
scraped_filename = "scraped_links.txt"
downloaded_filename = "downloaded_links.txt"
file_path = "."
download_path = "./downloads"
logs_directory = "./logs"
prefix = "PORN"
user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
)
downloader = "yt-dlp"
categories = []
sort_option = "mv"
date_filter = "w"
country_filter = "world"
max_videos = 1000

default_values = {
    "verbose": verbose,
    "websites": websites,
    "search_queries": search_queries,
    "scraped_filename": scraped_filename,
    "downloaded_filename": downloaded_filename,
    "file_path": file_path,
    "download_path": download_path,
    "logs_directory": logs_directory,
    "prefix": prefix,
    "user_agent": user_agent,
    "downloader": downloader,
    "categories": categories,
    "sort_option": sort_option,
    "date_filter": date_filter,
    "country_filter": country_filter,
    "max_videos": max_videos,
}

# Global variables
all_links = {}
total_link_counter = 0
total_per_website_link_counter = 0
total_per_query_link_counter = 0
total_per_category_link_counter = 0

videos_saved = 0
videos_failed = 0
videos_skipped = 0


def download_video(file_path, download_path, video_name, yt_dlp_path, ffmpeg_path, href):
    """
    Attempts to download a video with retries using yt-dlp or youtube-dl
    via subprocess.

    Args:
        file_path (str): Path to the file tracking downloaded links.
        download_path (str): The output template for the downloaded file.
        href (str): The URL of the video to download.
        title (str, optional): The title of the video (currently unused).
    """
    global total_link_counter
    global videos_saved
    global videos_failed
    global videos_skipped
    global debug_logger
    global download_logger

    # Check if the link has already been downloaded by reading line by line
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                for line in f:
                    if line.strip() == href:
                        message = f"Video already downloaded. Skipping: {href}"
                        output(message, debug_logger, Level.SKIP)
                        videos_skipped += 1
                        # Update remaining count here as we are skipping
                        remaining = (
                            total_link_counter
                            - videos_failed
                            - videos_saved
                            - videos_skipped
                        )
                        message = (
                            f"Videos Saved: {videos_saved}, Skipped: {videos_skipped}, Failed: {videos_failed}, "
                            f"Remaining: {remaining}, Total: {total_link_counter}\n"
                        )
                        output(message, debug_logger, Level.INFO)
                        return  # Exit the function as it's already downloaded
    except IOError as e:
        message = f"Error reading file {file_path}: {e}"
        output(message, debug_logger, Level.ERROR)
        # Continue attempting download in case reading failed but download might succeed

    max_retries = 10
    retry_delay_seconds = 5  # Optional: add a delay between retries

    for retry_count in range(max_retries):
        message = f"Attempt {retry_count + 1}/{max_retries} - Downloading video: {href}"
        output(message, debug_logger, Level.INFO)
        try:
            subprocess.run(
                [
                    yt_dlp_path,
                    "-P",
                    download_path,
                    "--extractor-args",
                    "generic:impersonate=chrome",
                    "--ffmpeg-location",
                    ffmpeg_path,
                    "-o",
                    video_name,
                    href,
                ],
                check=True,
            )
        except Exception as e:
            # Catch any other unexpected errors during the subprocess call or handling
            message = f"An unexpected error occurred during download attempt: {e}"
            output(message, debug_logger, Level.ERROR)

            if retry_count < max_retries - 1:
                message = f"Retrying in {retry_delay_seconds} seconds... (attempt {retry_count + 2}/{max_retries})"
                output(message, debug_logger, Level.WARNING)
                time.sleep(retry_delay_seconds)  # Wait before retrying
                continue  # Go to the next retry attempt
            else:
                message = "Maximum retries reached. Download failed."
                output(message, debug_logger, Level.ERROR)
                videos_failed += 1
                break  # Exit the retry loop after max retries

        # If we reach here, the download was successful
        message = "Download successful."
        output(message, debug_logger, Level.INFO)  # Log success to debug
        output(message, download_logger, Level.SUCCESS)  # Log success to download log

        # Save the link to the file *after* successful download
        try:
            with open(file_path, "a") as f:
                f.write(f"{href}\n")
        except IOError as e:
            message = f"Error writing downloaded link to file {file_path}: {e}"
            output(message, debug_logger, Level.ERROR)
            # Decide if this write failure should fail the whole download attempt
            # For now, we consider the download successful but log the file write issue.

        videos_saved += 1
        # Update remaining count after successful save
        remaining = total_link_counter - videos_failed - videos_saved - videos_skipped
        message = (
            f"Videos Saved: {videos_saved}, Skipped: {videos_skipped}, Failed: {videos_failed}, "
            f"Remaining: {remaining}, Total: {total_link_counter}\n"
        )
        output(message, debug_logger, Level.INFO)
        return  # Exit the function on success

    # This part is reached only if the download failed after all retries or if FileNotFoundError occurred
    remaining = total_link_counter - videos_failed - videos_saved - videos_skipped
    message = (
        f"Videos Saved: {videos_saved}, Skipped: {videos_skipped}, Failed: {videos_failed}, "
        f"Remaining: {remaining}, Total: {total_link_counter}\n"
    )
    output(message, debug_logger, Level.INFO)


def get_video_links(full_url, response, page_number, video_location, site_properties):
    global debug_logger
    raw_links = {}
    message = f"Parsing page {page_number}: {full_url}"
    output(message, debug_logger, Level.INFO)
    if "has_infinite_scroll" in site_properties:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        chrome_options = Options()
        chrome_options.add_argument("--headless")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(full_url)

        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll to the bottom of the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for new content to load
            time.sleep(2)

            # Calculate new scroll height and compare with the last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # If no more content is loaded, exit the loop
                soup = BeautifulSoup(response.content, "html.parser")
                try:
                    raw_links = soup.select(video_location)
                except Exception:
                    message = f"Couldn't found video links on site {full_url}\n"
                    output(message, debug_logger, Level.ERROR)
                    return None
                break

            last_height = new_height

    else:
        soup = BeautifulSoup(response, "html.parser")
        try:
            raw_links = soup.select(video_location)
        except Exception:
            message = f"Couldn't found video links on site {full_url}\n"
            output(message, debug_logger, Level.ERROR)
            return None

    links = []  # Create a new array to store modified links
    for link in raw_links:
        href = link.get("href")
        if href is not None and "javascript:void(0)" not in href:
            if href.startswith("/"):
                href = urljoin(full_url, href)
            links.append(href)
    return links


def pre_pre_get_links(
    query=None,
    category=None,
    **kwargs,
):
    page = 1
    while True:
        all_links, result = pre_get_links(
            query,
            category,
            page,
            **kwargs,
        )

        if result:
            page += 1
        else:
            break

    return all_links


def pre_get_links(
    query,
    category,
    page,
    **kwargs,
):
    global debug_logger
    result = True
    # Assuming max_pages is defined somewhere
    website_count = range(len(kwargs["names"]))
    for i in website_count:
        website_name = kwargs["names"][i]
        kwargs["max_page_site"].setdefault(website_name, None)
        message = f"Current website: {website_name}"
        output(message, debug_logger, Level.INFO)
        if kwargs["max_page_site"][website_name] is not None:
            if (
                page >= kwargs["max_page_site"][website_name]
                and kwargs["max_page_site"][website_name] != 0
            ):
                message = f"Max page reached for {website_name}: {kwargs['max_page_site'][website_name]}"
                output(message, debug_logger, Level.INFO)
                continue

        # Replace this in the future after click on button to next page is implemented
        if "{page}" not in kwargs["template_category_urls"][i] and page > 1:
            # continue
            pass

        global sort_option
        current_sort_options = None
        if kwargs["sort_options"][i]:
            if sort_option in kwargs["sort_options"][i]:
                current_sort_options = sort_option

        global date_filter
        current_date_filter_options = None
        if kwargs["date_filter_options"][i]:
            if date_filter in kwargs["date_filter_options"][i]:
                current_date_filter_options = date_filter

        global country_filter
        current_country_filter_options = None
        if kwargs["country_filter_options"][i]:
            if country_filter in kwargs["country_filter_options"][i]:
                current_country_filter_options = country_filter

        # Template handling
        global all_links

        # Prepare common parameters
        common_params = {
            "base_url": kwargs["base_urls"][i],
            "sort": current_sort_options,
            "date_filter": current_date_filter_options,
            "country_filter": current_country_filter_options,
            "page": page,
        }

        search_params = {}
        category_params = {}
        template = None  # Default to None

        # Search mode
        if kwargs["template_search_urls"][i] and query:
            all_links.setdefault(query, {}).setdefault(website_name, [])
            search_params = {"query": query}
            template = kwargs["template_search_urls"][i]

        # Category mode
        elif category and (
            kwargs["template_category_urls"][i]
            or kwargs["template_special_category_urls"][i]
        ):
            all_links.setdefault(category, {}).setdefault(website_name, [])

            if kwargs["names"][i] == "PornHub":
                category_params = {"category": get_category_number(category)}
            else:
                category_params = {"category": category}

            if (
                kwargs["category_specials"][i]
                and kwargs["template_special_category_urls"][i]
            ):
                if category in kwargs["category_specials"][i]:
                    template = kwargs["template_special_category_urls"][i]
                else:
                    template = kwargs["template_category_urls"][i]
            else:
                template = kwargs["template_category_urls"][i]

        # Fallback when neither query nor category are used
        else:
            all_links.setdefault(website_name, [])

        # Safely format URL
        full_url = template.format(
            **common_params,
            **search_params,
            **category_params,
        )

        response = retry_request(full_url.replace(" ", "+"), user_agent, debug_logger)
        if response:
            if page == 1 and kwargs["pre_click_actions"][i]:
                from selenium import webdriver
                from selenium.webdriver.common.by import By
                from selenium.webdriver.chrome.service import Service as ChromeService
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.common.exceptions import TimeoutException
                from webdriver_manager.chrome import ChromeDriverManager

                # Set Chrome options for headless mode
                options = webdriver.ChromeOptions()
                options.add_argument(
                    "--headless=new"
                )  # Use "--headless" for older versions if needed
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

                # Setup the Chrome driver with headless options
                driver = webdriver.Chrome(
                    service=ChromeService(ChromeDriverManager().install()),
                    options=options,
                )

                try:
                    message = f"Opening {kwargs['base_urls'][i]} in browser and doing click on {kwargs['pre_click_actions'][i]}"
                    output(message, debug_logger, Level.INFO)

                    driver.get(kwargs["base_urls"][i])

                    # Wait until the page is fully loaded
                    WebDriverWait(driver, 30).until(
                        lambda d: d.execute_script("return document.readyState")
                        == "complete"
                    )

                    # Find and click the element
                    element_locator = (
                        By.CSS_SELECTOR,
                        kwargs["pre_click_actions"][i],
                    )
                    element_to_click = driver.find_element(*element_locator)
                    element_to_click.click()
                    print("Element clicked successfully!")

                    # Optionally, wait for the page to change after click
                    WebDriverWait(driver, 30).until(EC.staleness_of(element_to_click))

                except TimeoutException:
                    print(
                        "Timed out waiting for the page to load or the element to update."
                    )
                except Exception as e:
                    print(f"An error occurred: {e}")
                finally:
                    driver.quit()

            links = get_video_links(
                full_url,
                response,
                page,
                kwargs["video_locations"][i],
                kwargs["site_properties"][i],
            )

            if website_name == "Bellesa":
                links = bellesa_links_filter(links)

            message = f"Found {len(links)} links on page {page}"
            output(message, debug_logger, Level.SUCCESS)

            # If there are no more pages, break the loop
            if links:
                if query:
                    all_links[query][website_name].extend(links)
                elif category:
                    all_links[category][website_name].extend(links)
                else:
                    all_links[website_name].extend(links)
                scrape_count = 0
                with open(kwargs["scraped_file_path"], "a+") as f:
                    f.seek(0)
                    for link in links:
                        if link not in f.read():
                            f.write(link + "\n")
                            global total_link_counter
                            total_link_counter += 1
                            if total_link_counter >= max_videos:
                                message = f"Max videos reached: {max_videos}"
                                output(message, debug_logger, Level.INFO)
                                result = False
                                break
                        else:
                            scrape_count += 1
                    if scrape_count != 0:
                        message = f"{scrape_count} link(s) already in scraped list file. Skipping...\n"
                        output(message, debug_logger, Level.SKIP)
                    else:
                        print("\n")

                    if result is False:
                        continue
                message = f"Total links found: {total_link_counter}"
                output(message, debug_logger, Level.INFO)
            else:
                # del all_links
                kwargs["max_page_site"][website_name] = page - 1
                message = f"No links found from {full_url}"
                output(message, debug_logger, Level.WARNING)
                result = False
        else:
            kwargs["max_page_site"][website_name] = page - 1
            message = f"No response from {full_url}"
            output(message, debug_logger, Level.WARNING)
    return all_links, result


def bellesa_links_filter(links):
    # Filter bellesa links
    # Set to store unique links
    unique_links = set()

    # Regular expression to match 'videos/' followed by a number
    pattern = re.compile(r"videos/\d+")

    # Filter links
    filtered_links = []
    for link in links:
        if pattern.search(link) and link not in unique_links:
            unique_links.add(link)
            filtered_links.append(link)
    return filtered_links


def get_bellesa_url(url):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    # Set up Chrome options to suppress logging
    chrome_options = Options()
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("window-size=1280,720")

    # Set up Selenium with Chrome WebDriver
    sys.stderr = open(os.devnull, "w")
    driver_path = "C:/Programs/chromedriver_win32/chromedriver.exe"
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open the URL
    driver.get(url)

    # Wait until the page is fully loaded
    try:
        # Adjust the timeout and the condition as needed
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except Exception as e:
        print(f"Error occurred while waiting for the page to load: {e}")

    # Get page content and parse with BeautifulSoup
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Extract the title from the <h2> tag
    title = None
    h2_tag = soup.find("h2")
    if h2_tag:
        title = h2_tag.get_text(strip=True)

    # Find all 'source' tags with 'src' ending with '.mp4'
    mp4_links = []
    for source in soup.find_all("source", src=True):
        link = source["src"]

        if link.endswith(".mp4"):
            # Add 'https://' to the link if it's missing
            if not link.startswith("http"):
                link = "https://" + link.lstrip("/")

            # Replace '480' before '.mp4' with '720'
            if "480" in link:
                link = link.replace("480.mp4", "720.mp4")

            mp4_links.append(link)

    if mp4_links != []:
        link = mp4_links[0]
        message = f"Found link: {link}"
        output(message, debug_logger, Level.INFO)
    else:
        message = "Link not found."
        output(message, debug_logger, Level.ERROR)

    # Close the browser
    driver.quit()

    return link, title


def start_porn_downloader():
    # Start timer
    start_time = datetime.now()

    global config_file
    global default_values

    # Assign values using dict.get()
    config = read_configuration(config_file)

    for var_name, default_value in default_values.items():
        globals()[var_name] = config.get(var_name, default_value)

    # Loading and parsing command-line arguments
    args = create_parser()
    arg_processors = {
        "websites": lambda val: (val.split(",") if isinstance(val, str) else []),
        "search_queries": lambda val: (val.split(",") if isinstance(val, str) else []),
    }
    overrideable_vars = list(default_values.keys())
    for var_name in overrideable_vars:
        if hasattr(args, var_name):
            arg_value = getattr(args, var_name)
            if arg_value is not None:
                processor = arg_processors.get(var_name)

                if processor:
                    globals()[var_name] = processor(arg_value)
                else:
                    globals()[var_name] = arg_value

    # Create and configure Loggers
    global debug_logger, download_logger
    debug_logger, download_logger = initialize_logs(logs_directory, prefix)
    message = "Script started."
    output(message, debug_logger, Level.INFO)

    yt_dlp_path = download_tool("yt-dlp", os.getcwd())
    ffmpeg_path = download_tool("ffmpeg", os.getcwd())
    message = f"YT-DLP Path: {yt_dlp_path}"
    output(message, debug_logger, Level.INFO)

    # Loading variables
    max_page_site = {}
    file_path = default_values["file_path"]
    scraped_file_path = os.path.join(file_path, scraped_filename)
    downloaded_file_path = os.path.join(file_path, downloaded_filename)

    file_paths = [scraped_file_path, downloaded_file_path]
    for file_path in file_paths:
        if not os.path.exists(file_path):
            open(file_path, "a").close()

    # Initialize lists
    names = []
    base_urls = []
    template_search_urls = []
    template_overview_urls = []
    template_category_urls = []
    template_special_category_urls = []
    category_options = []
    category_specials = []
    sort_parameters = []
    sort_options = []
    date_filter_parameters = []
    date_filter_options = []
    country_filter_parameters = []
    country_filter_options = []
    video_locations = []
    pre_click_actions = []
    site_properties = []
    search_query_parameters = []
    url_suffixes = []

    def append_values(entry):
        mappings = [
            ("name", names),
            ("base_url", base_urls),
            ("template_search_url", template_search_urls),
            ("template_overview_url", template_overview_urls),
            ("template_category_url", template_category_urls),
            ("template_special_category_url", template_special_category_urls),
            ("category_option", category_options),
            ("category_special", category_specials),
            ("sort_parameter", sort_parameters),
            ("sort_option", sort_options),
            ("date_filter_parameter", date_filter_parameters),
            ("date_filter_option", date_filter_options),
            ("country_filter_parameter", country_filter_parameters),
            ("country_filter_option", country_filter_options),
            ("video_location", video_locations),
            ("pre_click_action", pre_click_actions),
            ("site_property", site_properties),
            ("search_query_parameter", search_query_parameters),
            ("url_suffix", url_suffixes),
        ]

        for key, lst in mappings:
            lst.append(entry.get(key, None))

    # Load data from JSON file
    with open(WEBSITES_JSON_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    global websites
    for website in websites:
        if website == "all" and len(websites) == 1:
            for i, entry in enumerate(data):
                if i != len(data) - 1:
                    append_values(entry)
        else:
            for entry in data:
                if entry.get("name", "").lower() == website.lower():
                    append_values(entry)

    message = f"Websites: {names}"
    output(message, debug_logger, Level.INFO)
    message = f"Search Queries: {search_queries}"
    output(message, debug_logger, Level.INFO)
    message = f"Categories: {categories}"
    output(message, debug_logger, Level.INFO)
    message = f"Download path: {download_path}"
    output(message, debug_logger, Level.INFO)
    message = f"File path: {file_path}"
    output(message, debug_logger, Level.INFO)
    message = f"Scraped filename: {scraped_filename}"
    output(message, debug_logger, Level.INFO)
    message = f"Downloaded filename: {downloaded_filename}\n"
    output(message, debug_logger, Level.INFO)

    params = {
        "max_videos": max_videos,
        "names": names,
        "base_urls": base_urls,
        "template_search_urls": template_search_urls,
        "template_overview_urls": template_overview_urls,
        "template_category_urls": template_category_urls,
        "template_special_category_urls": template_special_category_urls,
        "category_specials": category_specials,
        "video_locations": video_locations,
        "pre_click_actions": pre_click_actions,
        "site_properties": site_properties,
        "sort_option": sort_option,
        "sort_options": sort_options,
        "date_filter": date_filter,
        "date_filter_options": date_filter_options,
        "country_filter": country_filter,
        "country_filter_options": country_filter_options,
        "max_page_site": max_page_site,
        "user_agent": user_agent,
        "scraped_file_path": scraped_file_path,
    }

    global all_links, total_per_query_link_counter, total_per_category_link_counter

    def fetch_links(query=None, category=None):
        global all_links
        page = 1
        total_before = len(all_links)
        while True:
            all_links, result = pre_get_links(
                query=query,
                category=category,
                page=page,
                **params,
            )
            if not result:
                break
            page += 1
        return len(all_links) - total_before

    # Handle search queries
    if search_queries:
        for query in search_queries:
            formatted_query = query.replace(" ", "+")
            all_links.setdefault(query, {})
            total_per_query_link_counter += fetch_links(query=formatted_query)

    # Handle categories
    if categories:
        for category in categories:
            all_links.setdefault(category, {})
            total_per_category_link_counter += fetch_links(category=category)

    # Fallback: no search queries or categories
    if not search_queries and not categories:
        fetch_links()

    # Download the videos
    def build_video_name(website, tag=None):
        base = f"[{website}]"
        if tag:
            base += f" [{tag}]"
        return base + " [%(channel)s] %(title)s [%(id)s].%(ext)s"

    is_query_mode = bool(search_queries)
    is_category_mode = bool(categories)

    base_download_root = download_path

    for key, websites in all_links.items():
        # Determine the tag to include in video name
        if is_query_mode:
            tag = key  # query string
        elif is_category_mode:
            tag = key.capitalize() if isinstance(key, str) else key
        else:
            tag = None  # fallback mode

        for website, links in websites.items():
            for link in links:
                destination_dir = os.path.join(
                    base_download_root, f"{tag} - {website}" if tag else website
                )
                os.makedirs(destination_dir, exist_ok=True)
                video_name = build_video_name(website, tag)
                download_video(
                    file_path,
                    destination_dir,
                    video_name,
                    yt_dlp_path,
                    ffmpeg_path,
                    link,
                )

    # Stop timer
    end_time = datetime.now()

    # Calculate script running time
    time_difference = str(end_time - start_time)
    message = (
        f"Script finished. Duration: {time_difference}, Downloads: {str(videos_saved)}"
    )
    output(message, debug_logger, Level.INFO)


if __name__ == "__main__":
    start_porn_downloader()
