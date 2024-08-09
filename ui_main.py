import logging
import json
import os
import sqlite3

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMenuBar, QTabWidget, QWidget, QVBoxLayout, QLabel, QDialog,
    QRadioButton, QPushButton, QTextEdit, QComboBox, QHBoxLayout, QLineEdit, QListWidget, QFileDialog,
    QSpacerItem, QSizePolicy, QTableWidget, QTableWidgetItem, QMessageBox, QFormLayout
)
from PySide6.QtCore import QThread, Signal, QObject, QUrl, QProcess, QTimer
from PySide6.QtGui import QAction
import configparser
from setup import install_steamcmd, install_pz_server
from browser_engine import BrowserEngine
from file_manager import ensure_config_exists
from page_analizer import SteamWorkshopIdentifier
import getpass

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
            logger.error(f"Error during SteamCMD installation: {e}")
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
            self.log.emit(
                f"Starting Project Zomboid server installation in {self.install_dir} using SteamCMD from {self.steamcmd_path}")
            install_pz_server(self.log.emit, self.steamcmd_path, self.install_dir, self.config_path)
        except Exception as e:
            logger.error(f"Error during Project Zomboid server installation: {e}")
            self.log.emit(f"Error during Project Zomboid server installation: {e}")
        self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self, server_directory=None):
        super().__init__()
        self.config_path = 'config.ini'
        self.config = configparser.ConfigParser()
        ensure_config_exists(self.config_path)  # Проверка и создание config.ini
        self.load_config()
        self.server_directory = server_directory or self.config.get('Paths', 'PZServer',
                                                                    fallback="C:/default/server/directory")
        self.zomboid_directory = self.get_zomboid_directory()  # Получаем путь к папке Zomboid
        self.setWindowTitle('Project Zomboid Mod Manager')
        self.setGeometry(100, 100, 1440, 720)

        # История навигации
        self.history = []
        self.history_index = -1

        # Reading settings from config.ini
        self.current_theme = self.config.get('Settings', 'theme', fallback='Light')

        # Applying the theme
        self.apply_theme(self.current_theme)

        # Creating the menu bar
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # Adding File menu
        self.file_menu = self.menu_bar.addMenu('File')

        # Adding actions to File menu
        self.settings_action = QAction('Settings', self)
        self.settings_action.triggered.connect(self.open_settings)
        self.file_menu.addAction(self.settings_action)

        self.options_action = QAction('Options', self)
        self.options_action.triggered.connect(self.open_options)
        self.file_menu.addAction(self.options_action)

        # Adding separator and Exit action
        self.file_menu.addSeparator()
        self.exit_action = QAction('Exit', self)
        self.exit_action.triggered.connect(self.exit_app)
        self.file_menu.addAction(self.exit_action)

        # Creating tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.add_tab("Server Setup", self.create_server_setup_tab)
        self.add_tab("Server", self.create_server_tab)
        self.add_tab("Mod Manager", self.create_mod_manager_tab)
        self.add_tab("Steam Workshop", self.create_steam_workshop_tab)
        self.add_tab("LocalNet")
        self.add_tab("Players Database", self.create_players_database_tab)

        self.process = None  # Переменная для процесса сервера

    def load_config(self):
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)

    def save_config(self):
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

    def add_tab(self, title, content_function=None):
        tab = QWidget()
        layout = QHBoxLayout()  # Используем QHBoxLayout для основной вкладки
        if content_function:
            content_function(layout)
        else:
            layout.addWidget(QLabel(f"This is the {title} tab"))
        tab.setLayout(layout)
        self.tabs.addTab(tab, title)

    def get_zomboid_directory(self):
        username = getpass.getuser()
        zomboid_path = f"C:/Users/{username}/Zomboid"
        return zomboid_path

    def create_server_setup_tab(self, layout):
        top_layout = QHBoxLayout()  # Горизонтальное расположение для верхнего макета

        # Левый макет для кнопок
        button_layout = QVBoxLayout()
        button_layout.setSpacing(5)  # Минимальное расстояние между кнопками
        button_layout.setContentsMargins(10, 10, 10, 10)  # Отступы от края

        install_steamcmd_button = QPushButton("Install SteamCMD")
        install_steamcmd_button.setFixedWidth(200)  # Фиксированная ширина кнопок
        install_steamcmd_button.clicked.connect(self.install_steamcmd)
        button_layout.addWidget(install_steamcmd_button)

        install_pz_server_button = QPushButton("Install Project Zomboid Dedicated Server")
        install_pz_server_button.setFixedWidth(200)
        install_pz_server_button.clicked.connect(self.install_pz_server)
        button_layout.addWidget(install_pz_server_button)

        test_start_pz_server_button = QPushButton("Test start Project Zomboid Dedicated Server")
        test_start_pz_server_button.setFixedWidth(200)
        button_layout.addWidget(test_start_pz_server_button)

        self.server_start_combobox = QComboBox()
        self.server_start_combobox.addItems(["StartServer32", "StartServer64", "StartServer64_nosteam"])
        self.server_start_combobox.setCurrentIndex(1)
        self.server_start_combobox.setFixedWidth(200)
        button_layout.addWidget(self.server_start_combobox)

        test_start_pz_server_button.clicked.connect(self.test_start_pz_server)

        # Добавляем вертикальный спейсер после кнопок, чтобы они оставались наверху
        button_layout.addStretch(1)

        # Добавляем button_layout к левому краю top_layout
        top_layout.addLayout(button_layout)

        # Создаем макет для консоли
        console_layout = QVBoxLayout()
        self.server_setup_console = QTextEdit()
        self.server_setup_console.setReadOnly(True)
        console_layout.addWidget(self.server_setup_console, stretch=1)

        self.console_input = QLineEdit()
        self.console_input.returnPressed.connect(self.send_command_to_server)  # Обработка ввода команд
        console_layout.addWidget(self.console_input)

        # Добавляем console_layout к правому краю top_layout
        top_layout.addLayout(console_layout, stretch=3)

        # Добавляем top_layout к основному layout
        layout.addLayout(top_layout)

    def install_steamcmd(self):
        program_directory = os.path.dirname(os.path.abspath(__file__))
        user_directory = self.get_user_directory()

        if not user_directory:
            self.append_to_console("Installation cancelled.")
            return

        logger.info(f"Installing SteamCMD to {user_directory}")
        self.save_path_to_config('Paths', 'SteamCMD', user_directory)

        self.thread = QThread()
        self.worker = Worker(program_directory, user_directory, self.config_path)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.log.connect(self.append_to_console)

        self.thread.start()

    def install_pz_server(self):
        user_directory = self.get_user_directory()
        steamcmd_path = self.config.get('Paths', 'SteamCMD', fallback='')

        if not user_directory:
            self.append_to_console("Installation cancelled.")
            return

        if not steamcmd_path or not os.path.exists(steamcmd_path):
            self.append_to_console("Error: SteamCMD not installed. Please install SteamCMD first.")
            return

        logger.info(f"Installing Project Zomboid server to {user_directory} using SteamCMD from {steamcmd_path}")
        self.save_path_to_config('Paths', 'PZServer', user_directory)

        self.server_directory = user_directory  # Обновляем путь к серверу

        self.thread = QThread()
        self.pz_worker = PZServerWorker(steamcmd_path, user_directory, self.config_path)
        self.pz_worker.moveToThread(self.thread)

        self.thread.started.connect(self.pz_worker.run)
        self.pz_worker.finished.connect(self.thread.quit)
        self.pz_worker.finished.connect(self.pz_worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.pz_worker.log.connect(self.append_to_console)

        self.thread.start()

    def save_path_to_config(self, section, option, path):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, path)
        self.save_config()
        logger.info(f"Saved {option} path to config: {path}")

    def append_to_console(self, text):
        self.server_setup_console.append(text)
        self.server_setup_console.ensureCursorVisible()  # Обеспечивает прокрутку консоли к последнему сообщению
        logger.debug(text)

    def get_user_directory(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        if dialog.exec():
            return dialog.selectedFiles()[0]
        return None

    def create_server_tab(self, layout):
        server_tabs = QTabWidget()

        server_tab = QWidget()
        server_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        start_server_button = QPushButton("Start Server")
        save_and_quit_button = QPushButton("Save and Quit")
        terminate_server_button = QPushButton("Terminate Server")

        start_server_button.clicked.connect(self.start_server)
        save_and_quit_button.clicked.connect(self.save_and_quit)
        terminate_server_button.clicked.connect(self.terminate_server)

        self.server_start_combobox_server_tab = QComboBox()
        self.server_start_combobox_server_tab.addItems(["StartServer32", "StartServer64", "StartServer64_nosteam"])
        self.server_start_combobox_server_tab.setCurrentIndex(1)

        left_layout.addWidget(start_server_button)
        left_layout.addWidget(save_and_quit_button)
        left_layout.addWidget(terminate_server_button)
        left_layout.addWidget(self.server_start_combobox_server_tab)

        player_list_label = QLabel("Player List")
        self.player_list = QListWidget()
        left_layout.addWidget(player_list_label)
        left_layout.addWidget(self.player_list)

        server_layout.addLayout(left_layout)

        console_layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        console_layout.addWidget(self.console)

        self.console_input_server_tab = QLineEdit()  # Определяем здесь, чтобы избежать ошибок
        self.console_input_server_tab.returnPressed.connect(self.send_command_to_server)
        console_layout.addWidget(self.console_input_server_tab)

        server_layout.addLayout(console_layout, stretch=1)

        server_tab.setLayout(server_layout)
        server_tabs.addTab(server_tab, "Server")

        advanced_settings_tab = QWidget()
        advanced_settings_layout = QVBoxLayout()
        advanced_settings_layout.addWidget(QLabel("This is the Advanced Settings tab"))
        advanced_settings_tab.setLayout(advanced_settings_layout)
        server_tabs.addTab(advanced_settings_tab, "Advanced Settings")

        config_settings_tab = QWidget()
        config_settings_layout = QVBoxLayout()
        config_settings_layout.addWidget(QLabel("This is the Config Settings tab"))
        config_settings_tab.setLayout(config_settings_layout)
        server_tabs.addTab(config_settings_tab, "Config Settings")

        layout.addWidget(server_tabs)

    def create_mod_manager_tab(self, layout):
        # Left spacer
        left_spacer = QVBoxLayout()
        left_spacer.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(left_spacer, stretch=1)

        # Left list and label
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Active Mods"))
        self.active_mods_list = QListWidget()
        left_layout.addWidget(self.active_mods_list)
        layout.addLayout(left_layout, stretch=2)

        # Button layout
        button_layout = QVBoxLayout()
        move_right_button = QPushButton(">>")
        move_left_button = QPushButton("<<")
        save_preset_button = QPushButton("Save Preset")
        load_preset_button = QPushButton("Load Preset")
        reset_to_default_button = QPushButton("Reset To Default")
        remove_mod_button = QPushButton("Remove Mod")
        remove_all_mods_button = QPushButton("Remove All Mods")

        # Find the widest button and set a fixed width for all buttons
        buttons = [move_right_button, move_left_button, save_preset_button, load_preset_button,
                   reset_to_default_button, remove_mod_button, remove_all_mods_button]
        max_button_width = max(button.sizeHint().width() for button in buttons)
        for button in buttons:
            button.setFixedWidth(max_button_width)

        button_layout.addWidget(move_right_button)
        button_layout.addWidget(move_left_button)
        button_layout.addWidget(save_preset_button)
        button_layout.addWidget(load_preset_button)
        button_layout.addWidget(reset_to_default_button)
        button_layout.addWidget(remove_mod_button)
        button_layout.addWidget(remove_all_mods_button)

        layout.addLayout(button_layout, stretch=1)

        # Right list and label
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Inactive Mods"))
        self.inactive_mods_list = QListWidget()
        right_layout.addWidget(self.inactive_mods_list)
        layout.addLayout(right_layout, stretch=2)

        move_right_button.clicked.connect(self.move_mod_to_active)
        move_left_button.clicked.connect(self.move_mod_to_inactive)

    def move_mod_to_active(self):
        current_item = self.inactive_mods_list.takeItem(self.inactive_mods_list.currentRow())
        if current_item:
            self.active_mods_list.addItem(current_item)

    def move_mod_to_inactive(self):
        current_item = self.active_mods_list.takeItem(self.active_mods_list.currentRow())
        if current_item:
            self.inactive_mods_list.addItem(current_item)

    def add_mod(self):
        current_url = self.browser.url().toString()
        identifier = SteamWorkshopIdentifier()
        try:
            logger.info(f"Checking URL: {current_url}")
            result = identifier.check_url(current_url)

            # Инициализация переменных
            page_type = None
            mod_name = None
            workshop_id = ""
            mod_id = ""
            map_folder = ""

            # Поиск необходимых значений по ключевым словам
            for item in result:
                if "Page Type:" in item:
                    page_type = item.split(":", 1)[1].strip()
                elif "Mod Name:" in item:
                    mod_name = item.split(":", 1)[1].strip()
                    logger.info(f"Mod name found: {mod_name}")
                elif "Workshop ID:" in item:
                    workshop_id = item.split(":", 1)[1].strip()
                elif "Mod ID:" in item:
                    mod_id = item.split(":", 1)[1].strip()
                elif "Map Folder:" in item:
                    map_folder = item.split(":", 1)[1].strip()

            if not page_type or not mod_name or not workshop_id:
                raise ValueError("Page Type, Mod Name, or Workshop ID not found in the result.")

            # Загрузка существующих данных из базы
            mods_db_path = 'modsdb.json'
            if os.path.exists(mods_db_path):
                with open(mods_db_path, 'r', encoding='utf-8') as file:
                    try:
                        mods_db = json.load(file)
                    except json.JSONDecodeError:
                        mods_db = []
            else:
                mods_db = []

            # Проверка на дублирование по Workshop ID
            for mod in mods_db:
                if workshop_id in mod.get('Workshop ID', []):
                    # Сообщение пользователю о том, что мод уже установлен
                    self.append_to_console(f"Mod already installed: {mod_name} (Workshop ID: {workshop_id})")
                    logger.info(f"Mod already installed: {mod_name} (Workshop ID: {workshop_id})")

                    # Создание всплывающего окна для уведомления
                    QMessageBox.information(self, "Mod Already Installed",
                                            f"The mod '{mod_name}' (Workshop ID: {workshop_id}) is already installed.")
                    return

            # Формирование данных для нового мода
            mod_data = {
                'url': current_url,
                'type': page_type,
                'name': mod_name,
                'Workshop ID': [workshop_id.strip()],
                'Mod ID': [id.strip() for id in mod_id.split(",") if id.strip()],
                'Map Folder': [folder.strip() for folder in map_folder.split(",") if folder.strip()]
            }

            # Сохранение новых данных
            mods_db.append(mod_data)
            with open(mods_db_path, 'w', encoding='utf-8') as file:
                json.dump(mods_db, file, ensure_ascii=False, indent=4)

            self.append_to_console(f"Mod added: {mod_data}")
            logger.info(f"Mod added: {mod_data}")
        except Exception as e:
            self.append_to_console(f"Failed to add mod: {str(e)}")
            logger.error(f"Failed to add mod: {str(e)}")

    def create_steam_workshop_tab(self, layout):
        side_layout = QVBoxLayout()

        button_layout = QHBoxLayout()
        back_button = QPushButton("<-")
        home_button = QPushButton("Home")
        forward_button = QPushButton("->")

        button_layout.addWidget(back_button)
        button_layout.addWidget(home_button)
        button_layout.addWidget(forward_button)

        side_layout.addLayout(button_layout)

        self.player_list = QListWidget()
        side_layout.addWidget(self.player_list)

        add_mod_button = QPushButton("Add Mod")
        side_layout.addWidget(add_mod_button)

        layout.addLayout(side_layout, stretch=1)

        self.browser = BrowserEngine()
        layout.addWidget(self.browser, stretch=3)

        # Подключение кнопок к функциям
        back_button.clicked.connect(self.navigate_back)
        home_button.clicked.connect(self.navigate_home)
        forward_button.clicked.connect(self.navigate_forward)

        # Обработка события загрузки URL
        self.browser.urlChanged.connect(lambda url: self.add_to_history(url.toString()))

        add_mod_button.clicked.connect(self.add_mod)

    def navigate_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            url = self.history[self.history_index]
            self.browser.setUrl(QUrl(url))
            logger.info(f"Navigating back to: {url}")

    def navigate_home(self):
        home_url = "https://steamcommunity.com/app/108600/workshop/"
        self.browser.setUrl(QUrl(home_url))
        logger.info(f"Navigating to home: {home_url}")

        # Обновляем историю навигации
        if self.history_index == -1 or self.history[self.history_index] != home_url:
            self.history.append(home_url)
            self.history_index += 1

    def navigate_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            url = self.history[self.history_index]
            self.browser.setUrl(QUrl(url))
            logger.info(f"Navigating forward to: {url}")

    def add_to_history(self, url):
        if self.history_index == -1 or self.history[self.history_index] != url:
            # Удаляем все элементы впереди, если мы перемещаемся на новую страницу
            self.history = self.history[:self.history_index + 1]
            self.history.append(url)
            self.history_index += 1
            logger.info(f"Added to history: {url}")

    def create_players_database_tab(self, layout):
        self.db_path = os.path.join(self.zomboid_directory, 'db', 'servertest.db')
        if not os.path.exists(self.db_path):
            logger.error(f"Database file not found: {self.db_path}")
            return

        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        self.tables = self.cursor.fetchall()
        if not self.tables:
            logger.error("No tables found in database.")
            self.connection.close()
            return

        self.tab_widget = QTabWidget()
        for table in self.tables:
            table_name = table[0]
            tab = QWidget()
            tab_layout = QVBoxLayout()

            self.cursor.execute(f"PRAGMA table_info({table_name});")
            columns = self.cursor.fetchall()
            column_names = [column[1] for column in columns]

            table_widget = QTableWidget()
            self.cursor.execute(f"SELECT * FROM {table_name}")
            rows = self.cursor.fetchall()

            table_widget.setRowCount(len(rows))
            table_widget.setColumnCount(len(column_names))
            table_widget.setHorizontalHeaderLabels(column_names)

            for row_index, row in enumerate(rows):
                for col_index, cell in enumerate(row):
                    table_widget.setItem(row_index, col_index, QTableWidgetItem(str(cell)))

            add_row_button = QPushButton("Add Row")
            add_row_button.clicked.connect(lambda ch, t=table_name, tw=table_widget: self.add_row(t, tw))

            delete_row_button = QPushButton("Delete Row")
            delete_row_button.clicked.connect(lambda ch, t=table_name, tw=table_widget: self.delete_row(t, tw))

            tab_layout.addWidget(table_widget)
            tab_layout.addWidget(add_row_button)
            tab_layout.addWidget(delete_row_button)
            tab.setLayout(tab_layout)
            self.tab_widget.addTab(tab, table_name)

        layout.addWidget(self.tab_widget)

    def add_row(self, table_name, table_widget):
        columns = [table_widget.horizontalHeaderItem(i).text() for i in range(table_widget.columnCount())]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Add Row to {table_name}")
        form_layout = QFormLayout()

        inputs = []
        for column in columns:
            line_edit = QLineEdit()
            form_layout.addRow(QLabel(column), line_edit)
            inputs.append(line_edit)

        add_button = QPushButton("Add")
        add_button.clicked.connect(lambda: self.commit_add_row(dialog, table_name, inputs, table_widget))
        form_layout.addWidget(add_button)

        dialog.setLayout(form_layout)
        dialog.exec()

    def commit_add_row(self, dialog, table_name, inputs, table_widget):
        new_row = [input.text() for input in inputs]

        if len(new_row) != table_widget.columnCount():
            QMessageBox.warning(self, "Error", f"Please enter {table_widget.columnCount()} values.")
            return

        placeholders = ', '.join(['?'] * len(new_row))
        sql = f"INSERT INTO {table_name} VALUES ({placeholders})"

        try:
            self.cursor.execute(sql, new_row)
            self.connection.commit()
            table_widget.setRowCount(table_widget.rowCount() + 1)
            for col_index, cell in enumerate(new_row):
                table_widget.setItem(table_widget.rowCount() - 1, col_index, QTableWidgetItem(cell))
            dialog.accept()
        except sqlite3.IntegrityError as e:
            QMessageBox.warning(self, "Error", f"Failed to add row: {e}")

    def delete_row(self, table_name, table_widget):
        selected_row = table_widget.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "No row selected")
            return

        row_id = table_widget.item(selected_row, 0).text()  # Assuming the first column is the primary key
        self.cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (row_id,))
        self.connection.commit()

        table_widget.removeRow(selected_row)

    def send_command(self):
        command = self.console_input_server_tab.text()
        if command:
            self.console.append(f"> {command}")
            self.console_input_server_tab.clear()
            if self.process:
                self.process.write(f"{command}\n".encode())
        logger.info(f"Sent command: {command}")

    def send_command_to_server(self):
        command = self.console_input.text()
        if command:
            self.server_setup_console.append(f"> {command}")
            self.console_input.clear()
            if self.process:
                self.process.write(f"{command}\n".encode())
        logger.info(f"Sent command to server: {command}")

    def start_server(self):
        self.console.append("Starting Server...")
        logger.info("Starting server")
        if not self.process or self.process.state() != QProcess.Running:
            server_option = self.server_start_combobox_server_tab.currentText()
            server_file = f"{server_option}.bat"
            if not os.path.exists(os.path.join(self.server_directory, server_file)):
                error_message = f"Error: {server_file} not found in {self.server_directory}."
                self.console.append(error_message)
                logger.error(error_message)
                return

            self.process = QProcess(self)
            self.process.setProgram(os.path.join(self.server_directory, server_file))
            self.process.setProcessChannelMode(QProcess.MergedChannels)
            self.process.readyReadStandardOutput.connect(self.display_output)
            self.process.readyReadStandardError.connect(self.display_output)
            self.process.start()

    def display_output(self):
        output = self.process.readAllStandardOutput().data().decode('cp1251', errors='ignore')
        self.console.append(output)
        self.server_setup_console.append(output)
        logger.debug(f"Server output: {output}")

        if "SERVER STARTED" in output:
            QTimer.singleShot(10000, self.quit_server)
            logger.info("Server started. Scheduled quit command in 10 seconds.")
            self.save_path_to_config('Paths', 'Zomboid', self.zomboid_directory)

    def quit_server(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.write(b"quit\n")
            logger.info("Sent quit command to server.")

    def save_and_quit(self):
        self.console.append("Saving and Quitting...")
        logger.info("Saving and quitting server")
        if self.process and self.process.state() == QProcess.Running:
            self.process.write(b"save\n")
            self.process.write(b"quit\n")

    def terminate_server(self):
        self.console.append("Terminating Server...")
        logger.info("Terminating server")
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()

    def test_start_pz_server(self):
        self.load_config()  # Ensure we have the latest config values
        self.server_directory = self.config.get('Paths', 'PZServer', fallback="C:/default/server/directory")
        server_option = self.server_start_combobox.currentText()
        server_file = f"{server_option}.bat"

        if not os.path.exists(os.path.join(self.server_directory, server_file)):
            error_message = f"Error: {server_file} not found in {self.server_directory}."
            self.server_setup_console.append(error_message)
            logger.error(error_message)
            return

        self.process = QProcess(self)
        self.process.setProgram(os.path.join(self.server_directory, server_file))
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.display_output)
        self.process.readyReadStandardError.connect(self.display_output)
        logger.info(f"Starting server with {server_file} in {self.server_directory}")
        self.process.start()

    def open_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Settings")
        settings_dialog.setGeometry(100, 100, 300, 400)
        settings_dialog.exec()

    def open_options(self):
        options_dialog = QDialog(self)
        options_dialog.setWindowTitle("Options")
        options_dialog.setGeometry(100, 100, 300, 400)

        layout = QVBoxLayout()

        self.light_theme_rb = QRadioButton("Light")
        self.light_theme_rb.setChecked(self.current_theme == 'Light')
        layout.addWidget(self.light_theme_rb)

        self.light_dark_theme_rb = QRadioButton("Light Dark")
        self.light_dark_theme_rb.setChecked(self.current_theme == 'Light Dark')
        layout.addWidget(self.light_dark_theme_rb)

        self.dark_theme_rb = QRadioButton("Dark")
        self.dark_theme_rb.setChecked(self.current_theme == 'Dark')
        layout.addWidget(self.dark_theme_rb)

        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_and_save_theme)
        layout.addWidget(apply_button)

        options_dialog.setLayout(layout)
        options_dialog.exec()

    def apply_and_save_theme(self):
        if 'Settings' not in self.config:
            self.config['Settings'] = {}
        self.config.set('Settings', 'theme', self.current_theme)

        self.apply_theme(self.current_theme)

        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

    def apply_theme(self, theme):
        if theme == 'Light':
            self.setStyleSheet("")
        elif theme == 'Light Dark':
            self.setStyleSheet("QWidget { background-color: #aaaaaa; color: #000000; }")
        elif theme == 'Dark':
            self.setStyleSheet("QWidget { background-color: #333333; color: #ffffff; }")

    def exit_app(self):
        self.close()


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
