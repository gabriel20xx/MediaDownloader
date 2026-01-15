import os
import sys
import platform
import shutil
import zipfile
import tarfile
import urllib.request


def download_tool(tool: str, destination: str = ".") -> str:
    system = platform.system()
    os_map = {
        "Windows": {
            "yt-dlp": {
                "filename": "yt-dlp.exe",
                "url": "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe",
                "final_name": "yt-dlp",
            },
            "ffmpeg": {
                "archive": "ffmpeg.zip",
                "url": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
                "executable": "ffmpeg.exe",
            },
        },
        "Linux": {
            "yt-dlp": {
                "filename": "yt-dlp_linux",
                "url": "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux",
                "final_name": "yt-dlp",
            },
            "ffmpeg": {
                "archive": "ffmpeg.tar.xz",
                "url": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
                "executable": "ffmpeg",
            },
        },
    }

    if system not in os_map or tool not in os_map[system]:
        print(f"Unsupported OS or tool: {system} / {tool}")
        sys.exit(1)

    info = os_map[system][tool]

    if tool == "yt-dlp":
        final_path = os.path.join(destination, info["final_name"])
        if not os.path.isfile(final_path):
            print(f"Downloading {tool} from {info['url']}...")
            tmp_path = os.path.join(destination, info["filename"])
            try:
                urllib.request.urlretrieve(info["url"], tmp_path)
                os.chmod(tmp_path, 0o755)
                os.rename(tmp_path, final_path)
                print(f"{tool} downloaded and saved as '{info['final_name']}'")
            except Exception as e:
                print(f"Failed to download {tool}: {e}")
                sys.exit(1)
        else:
            print(f"{tool} already exists.")
        return final_path

    elif tool == "ffmpeg":
        exe_path = os.path.join(destination, info["executable"])
        if os.path.isfile(exe_path):
            print("FFmpeg already exists. Skipping download.")
            return exe_path

        archive_name = info["archive"]
        print(f"Downloading FFmpeg for {system}...")
        try:
            urllib.request.urlretrieve(info["url"], archive_name)
        except Exception as e:
            print(f"Failed to download FFmpeg: {e}")
            sys.exit(1)

        print("Extracting FFmpeg...")
        try:
            if archive_name.endswith(".zip"):
                with zipfile.ZipFile(archive_name, 'r') as zip_ref:
                    zip_ref.extractall(destination)
                    for root, _, files in os.walk(destination):
                        if info["executable"] in files:
                            shutil.copy(os.path.join(root, info["executable"]), exe_path)
                            break
            elif archive_name.endswith(".tar.xz"):
                with tarfile.open(archive_name, "r:xz") as tar_ref:
                    tar_ref.extractall(destination)
                    for root, _, files in os.walk(destination):
                        if info["executable"] in files and os.access(os.path.join(root, info["executable"]), os.X_OK):
                            shutil.copy(os.path.join(root, info["executable"]), exe_path)
                            os.chmod(exe_path, 0o755)
                            break
        except Exception as e:
            print(f"Failed to extract FFmpeg: {e}")
            sys.exit(1)

        print("Cleaning up...")
        os.remove(archive_name)
        print("FFmpeg installed successfully.")
        return exe_path
