# setup.py

import os
import subprocess
import shutil
import threading
import time
import configparser
from elevate import elevate
from network_manager import download_steamcmd, extract_zip

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

def create_install_bat(install_dir, steamcmd_path):
    bat_content = f"""
@echo off
"{steamcmd_path}\steamcmd.exe" +force_install_dir "{install_dir}" +login anonymous +app_update 380870 validate +quit
"""
    bat_path = os.path.join(install_dir, "install_pz_server.bat")
    with open(bat_path, 'w') as bat_file:
        bat_file.write(bat_content)
    return bat_path

def install_pz_server(console_output_func, steamcmd_path, install_dir, config_path):
    try:
        console_output_func("Installing Project Zomboid Dedicated Server...")
        os.makedirs(install_dir, exist_ok=True)

        bat_path = create_install_bat(install_dir, steamcmd_path)
        console_output_func(f"Created install script: {bat_path}")

        elevate()  # Elevate the process to run with administrator privileges

        process = subprocess.Popen(bat_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        stream_output(process, console_output_func)

        if process.returncode == 0:
            console_output_func(f"Project Zomboid Dedicated Server installed at: {install_dir}")
            # Удаляем install_pz_server.bat после успешной установки
            bat_path = bat_path+"/install_pz_server.bat"
            os.remove(bat_path)
            console_output_func(f"Deleted install script: {bat_path}")
        else:
            console_output_func(f"Installation failed with code: {process.returncode}")

    except Exception as e:
        console_output_func(f"Error: {str(e)}")
    finally:
        save_path(config_path, 'Paths', 'PZServer', install_dir)  # Сохраняем путь установки сервера перед завершением
        console_output_func("quit")

def ensure_config_exists(config_path):
    if not os.path.exists(config_path):
        config = configparser.ConfigParser()
        config.add_section('Paths')
        with open(config_path, 'w') as configfile:
            config.write(configfile)
