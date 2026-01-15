import argparse


def create_parser():
    # Create the parser
    parser = argparse.ArgumentParser(description="Downloader Script")
    parser.add_argument(
        "-w",
        "--websites",
        "--website",
        type=str,
        help="Specify the website or websites",
    )
    parser.add_argument("--filename", type=str, help="Filename for output file")
    parser.add_argument("--file_path", type=str, help="Output path for video links")
    parser.add_argument(
        "-dp", "--download_path", type=str, help="Output path for video files"
    )
    parser.add_argument("-q", "--queries", type=str, help="Search queries")
    parser.add_argument(
        "-ua", "--user_agent", type=str, help="Define custom user agent"
    )
    parser.add_argument(
        "-do",
        "--download_order",
        type=int,
        help="Define the download order with 1, 2 or 3",
    )
    parser.add_argument(
        "-mp",
        "--max_pages",
        type=int,
        help="The maximum pages it will query per website",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose mode"
    )
    parser.add_argument(
        "--level",
        type=str,
        choices=["INFO", "DEBUG", "ERROR"],
        help="Set logging level",
    )
    parser.add_argument(
        "--download_directory",
        type=str,
        help="Directory for downloads",
    )
    parser.add_argument(
        "--alternative_download_directory",
        type=str,
        help="Alternative download directory",
    )
    parser.add_argument(
        "--logs_directory",
        type=str,
        help="Directory for logs",
    )
    parser.add_argument(
        "--log_by_day", action="store_true", help="Enable logging by day"
    )
    parser.add_argument(
        "--resolution",
        type=str,
        choices=["1080p", "1080p.x265", "2160p"],
        help="Set video resolution",
    )
    parser.add_argument(
        "--languages",
        type=str,
        choices=["ENGLISH", "GERMAN", "SPANISH"],
        help="Set language",
    )
    parser.add_argument("--prefix", type=str, help="Set prefix")
    parser.add_argument(
        "--magnet_file",
        type=str,
        help="Magnet file location",
    )
    parser.add_argument(
        "--use_index_page",
        action="store_true",
        help="Enable use of index page",
    )
    parser.add_argument(
        "--use_search_queries",
        action="store_true",
        help="Enable use of search queries",
    )
    parser.add_argument(
        "--search_queries",
        type=str,
        nargs="+",
        help="List of search queries",
    )
    parser.add_argument(
        "--max_duration",
        type=str,
        nargs="+",
        help="Max script running duration in minutes",
    )
    parser.add_argument(
        "--delay",
        type=str,
        nargs="+",
        help="Delay between each request",
    )

    # Parse the arguments
    args = parser.parse_args()
    return args
