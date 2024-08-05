import os
import subprocess
import shutil
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from network_manager import download_steamcmd, extract_zip


class LogFileHandler(FileSystemEventHandler):
    def __init__(self, log_file_path, console_output_func):
        self.log_file_path = log_file_path
        self.console_output_func = console_output_func
        self.last_position = 0

    def on_modified(self, event):
        if event.src_path == self.log_file_path:
            with open(self.log_file_path, 'r') as f:
                f.seek(self.last_position)
                lines = f.readlines()
                self.last_position = f.tell()
                for line in lines:
                    self.console_output_func(line.strip())


def install_steamcmd(console_output_func, program_directory, user_directory, progress_callback):
    try:
        progress_callback(0, 100)
        console_output_func("Downloading SteamCMD...")
        zip_path = download_steamcmd(program_directory, progress_callback)
        console_output_func("SteamCMD downloaded.")
        progress_callback(20, 100)

        console_output_func("Extracting SteamCMD...")
        extract_dir = os.path.join(program_directory, "steamcmd")
        os.makedirs(extract_dir, exist_ok=True)
        extract_zip(zip_path, extract_dir)
        console_output_func("SteamCMD extracted.")
        progress_callback(40, 100)

        if not os.path.exists(user_directory):
            os.makedirs(user_directory)

        for item in os.listdir(extract_dir):
            s = os.path.join(extract_dir, item)
            d = os.path.join(user_directory, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

        console_output_func("SteamCMD moved to user directory.")
        progress_callback(60, 100)

        console_output_func("Installing SteamCMD...")
        steamcmd_path = os.path.join(user_directory, 'steamcmd.exe')

        log_dir = os.path.join(user_directory, 'logs')
        log_file_path = os.path.join(log_dir, 'bootstrap_log.txt')
        os.makedirs(log_dir, exist_ok=True)

        event_handler = LogFileHandler(log_file_path, console_output_func)
        observer = Observer()
        observer.schedule(event_handler, path=log_dir, recursive=False)
        observer.start()

        process = subprocess.Popen([steamcmd_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                console_output_func(output.strip())

        process.wait()
        observer.stop()
        observer.join()

        progress_callback(80, 100)
        console_output_func("SteamCMD installed.")

        os.remove(zip_path)
        shutil.rmtree(extract_dir)
        console_output_func("Cleanup complete.")
        progress_callback(100, 100)

    except Exception as e:
        console_output_func(f"Error: {str(e)}")
    finally:
        console_output_func("quit")
