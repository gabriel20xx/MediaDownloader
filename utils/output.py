import os
from datetime import datetime
from enum import Enum


class Color(Enum):
    RESET = '\033[0m'
    WHITE = '\033[97m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'


class Level(Enum):
    SUCCESS = "SUCCESS"
    SKIP = "SKIP"
    WARNING = "WARNING"
    ERROR = "ERROR"
    INFO = "INFO"


class Logger(Enum):
    DEBUG = "DEBUG"
    DOWNLOAD = "DOWNLOAD"


def initialize_logs(logs_directory, prefix):
    year = str(datetime.now().strftime("%Y"))
    month = str(datetime.now().strftime("%m"))
    day = str(datetime.now().strftime("%d"))
    date = f"{year}-{month}-{day}"
    directory_path = os.path.join(logs_directory, year, month, day)
    os.makedirs(directory_path, exist_ok=True)

    debug_log_file = os.path.join(directory_path, f"{date}-{prefix}Debug.log")
    download_log_file = os.path.join(directory_path, f"{date}-{prefix}Download.log")

    return debug_log_file, download_log_file


def log_message(message, log_file="../logs/log.txt", level=Level.INFO):
    current_time = datetime.now().strftime('%H:%M:%S')
    with open(log_file, "a") as file:
        file.write(f"\n[{current_time}] [{level.value}] {message}")


def output_message(message, level=Level.INFO):
    if level == Level.SUCCESS:
        color = Color.GREEN
    elif level == Level.SKIP:
        color = Color.CYAN
    elif level == Level.WARNING:
        color = Color.ORANGE
    elif level == Level.ERROR:
        color = Color.RED
    elif level == Level.INFO:
        color = Color.WHITE
    else:
        raise NotImplementedError

    current_time = datetime.now().strftime('%H:%M:%S')
    print(f"{color.value}[{current_time}] [{level.value}] {message}{Color.RESET.value}")


def output(message, log_file, level=Level.INFO):
    output_message(message, level)
    log_message(message, log_file, level)
