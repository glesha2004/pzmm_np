# setup.py

import os
import subprocess
import shutil
import threading
import time
from network_manager import download_steamcmd, extract_zip
import configparser

def tail_log_file(log_file_path, interval, console_output_func):
    time.sleep(5)  # Задержка перед началом чтения лог-файла
    try:
        with open(log_file_path, 'r', encoding='cp1251') as log_file:
            while True:
                line = log_file.readline()
                if not line:
                    time.sleep(interval)
                    continue
                console_output_func(line.strip())
    except Exception as e:
        console_output_func(f"Error reading log file: {str(e)}")

def stream_output(process, console_output_func):
    for line in iter(process.stdout.readline, ''):
        console_output_func(line.strip())
    for line in iter(process.stderr.readline, ''):
        console_output_func(line.strip())

def save_path(config_path, section, key, value):
    config = configparser.ConfigParser()
    config.read(config_path)
    if section not in config:
        config[section] = {}
    config[section][key] = value
    with open(config_path, 'w') as configfile:
        config.write(configfile)

def install_steamcmd(console_output_func, program_directory, user_directory, config_path):
    try:
        console_output_func("Downloading SteamCMD...")
        zip_path = download_steamcmd(program_directory, lambda x, y: None)
        console_output_func("SteamCMD downloaded.")

        console_output_func("Extracting SteamCMD...")
        extract_dir = os.path.join(program_directory, "steamcmd")
        os.makedirs(extract_dir, exist_ok=True)
        extract_zip(zip_path, extract_dir)
        console_output_func("SteamCMD extracted.")

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

        console_output_func("Installing SteamCMD...")
        steamcmd_path = os.path.join(user_directory, 'steamcmd.exe')
        log_file_path = os.path.join(user_directory, 'logs', 'bootstrap_log.txt')

        if not os.path.exists(steamcmd_path):
            console_output_func(f"SteamCMD not found at path {steamcmd_path}")
            return

        threading.Thread(target=tail_log_file, args=(log_file_path, 1, console_output_func)).start()

        process = subprocess.Popen([steamcmd_path, "+quit"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   encoding='cp1251')
        stream_output(process, console_output_func)

        if process.returncode == 0:
            console_output_func(f"SteamCMD installed at: {user_directory}")
        else:
            console_output_func(f"SteamCMD installation failed with code: {process.returncode}")

        save_path(config_path, 'Paths', 'SteamCMD', steamcmd_path)  # Сохраняем путь к steamcmd.exe

        os.remove(zip_path)
        shutil.rmtree(extract_dir)
        console_output_func("Cleanup complete.")

    except Exception as e:
        console_output_func(f"Error: {str(e)}")
    finally:
        console_output_func("quit")

def install_pz_server(console_output_func, steamcmd_path, install_dir, config_path):
    try:
        console_output_func("Installing Project Zomboid Dedicated Server...")
        os.makedirs(install_dir, exist_ok=True)

        script_content = """
force_install_dir {install_dir}
login anonymous
app_update 380870 validate
quit
""".format(install_dir=install_dir)

        script_path = os.path.join(install_dir, 'install_pz_server.txt')
        with open(script_path, 'w') as script_file:
            script_file.write(script_content)

        process = subprocess.Popen([steamcmd_path, '+runscript', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stream_output(process, console_output_func)

        if process.returncode == 0:
            console_output_func(f"Project Zomboid Dedicated Server installed at: {install_dir}")
        else:
            console_output_func(f"Installation failed with code: {process.returncode}")

        os.remove(script_path)
    except Exception as e:
        console_output_func(f"Error: {str(e)}")
    finally:
        save_path(config_path, 'Paths', 'PZServer', install_dir)  # Сохраняем путь установки сервера перед завершением
        console_output_func("quit")
