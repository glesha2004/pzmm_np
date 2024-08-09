import logging
from PySide6.QtCore import QObject, Signal
from setup import install_steamcmd, install_pz_server

class Worker(QObject):
    finished = Signal()
    log = Signal(str)

    def __init__(self, program_directory, user_directory, config_path):
        super().__init__()
        self.program_directory = program_directory
        self.user_directory = user_directory
        self.config_path = config_path

    def run(self):
        try:
            self.log.emit(f"Starting SteamCMD installation in {self.user_directory}")
            install_steamcmd(self.log.emit, self.program_directory, self.user_directory, self.config_path)
        except Exception as e:
            logging.error(f"Error during SteamCMD installation: {e}")
            self.log.emit(f"Error during SteamCMD installation: {e}")
        self.finished.emit()

class PZServerWorker(QObject):
    finished = Signal()
    log = Signal(str)

    def __init__(self, steamcmd_path, install_dir, config_path):
        super().__init__()
        self.steamcmd_path = steamcmd_path
        self.install_dir = install_dir
        self.config_path = config_path

    def run(self):
        try:
            self.log.emit(f"Starting Project Zomboid server installation in {self.install_dir} using SteamCMD from {self.steamcmd_path}")
            install_pz_server(self.log.emit, self.steamcmd_path, self.install_dir, self.config_path)
        except Exception as e:
            logging.error(f"Error during Project Zomboid server installation: {e}")
            self.log.emit(f"Error during Project Zomboid server installation: {e}")
        self.finished.emit()
