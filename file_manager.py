# file_manager.py

import os
import configparser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def ensure_config_exists(config_path):
    config = configparser.ConfigParser()

    # Секции и значения по умолчанию
    default_config = {
        'Settings': {
            'theme': 'Light'
        },
        'Paths': {
            'SteamCMD': ''
        }
    }

    # Если конфигурационный файл существует, читаем его
    if os.path.exists(config_path):
        config.read(config_path)

        # Проверка и добавление недостающих секций и параметров
        for section, params in default_config.items():
            if not config.has_section(section):
                config.add_section(section)
            for param, value in params.items():
                if not config.has_option(section, param):
                    config.set(section, param, value)
    else:
        # Если конфигурационный файл не существует, создаем его с значениями по умолчанию
        for section, params in default_config.items():
            config.add_section(section)
            for param, value in params.items():
                config.set(section, param, value)

    # Сохраняем изменения
    with open(config_path, 'w') as configfile:
        config.write(configfile)

class ModpackFolderHandler(FileSystemEventHandler):
    def __init__(self, modpacks_list_widget, modpacks_dir):
        self.modpacks_list_widget = modpacks_list_widget
        self.modpacks_dir = modpacks_dir

    def on_modified(self, event):
        if not event.is_directory:
            self.update_modpacks_list()

    def on_created(self, event):
        if not event.is_directory:
            self.update_modpacks_list()

    def on_deleted(self, event):
        if not event.is_directory:
            self.update_modpacks_list()

    def update_modpacks_list(self):
        """Обновляет список модпаков в модуле Mod Manager."""
        self.modpacks_list_widget.clear()

        if os.path.exists(self.modpacks_dir):
            for filename in os.listdir(self.modpacks_dir):
                if filename.endswith('.json'):
                    self.modpacks_list_widget.addItem(filename)
                    print(f"Loaded modpack: {filename}")
        else:
            print(f"Modpacks directory not found: {self.modpacks_dir}")

def start_modpack_observer(modpacks_list_widget, modpacks_dir):
    observer = Observer()
    modpack_handler = ModpackFolderHandler(modpacks_list_widget, modpacks_dir)
    observer.schedule(modpack_handler, modpacks_dir, recursive=False)
    observer.start()
    return observer