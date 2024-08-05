from PySide6.QtWidgets import QMainWindow, QMenuBar, QTabWidget, QWidget, QVBoxLayout, QLabel, QMenu, QDialog, \
    QRadioButton, QPushButton, QTextEdit, QComboBox, QHBoxLayout, QLineEdit, QListWidget, QSpacerItem, QSizePolicy
from PySide6.QtGui import QAction
import configparser
from browser_engine import BrowserEngine

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Project Zomboid Mod Manager')
        self.setGeometry(100, 100, 1440, 720)

        # Reading settings from config.ini
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
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

    def add_tab(self, title, content_function=None):
        tab = QWidget()
        layout = QHBoxLayout()
        if content_function:
            content_function(layout)
        else:
            layout.addWidget(QLabel(f"This is the {title} tab"))
        tab.setLayout(layout)
        self.tabs.addTab(tab, title)

    def create_server_setup_tab(self, layout):
        left_layout = QVBoxLayout()
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(0, 0, 0, 0)

        install_steamcmd_button = QPushButton("Install SteamCMD")
        install_steamcmd_button.clicked.connect(self.install_steamcmd)
        left_layout.addWidget(install_steamcmd_button)

        install_pz_server_button = QPushButton("Install Project Zomboid Dedicated Server")
        install_pz_server_button.clicked.connect(self.install_pz_server)
        left_layout.addWidget(install_pz_server_button)

        test_start_pz_server_button = QPushButton("Test start Project Zomboid Dedicated Server")
        left_layout.addWidget(test_start_pz_server_button)

        self.server_start_combobox = QComboBox()
        self.server_start_combobox.addItems(["StartServer32", "StartServer64", "StartServer64_nosteam"])
        self.server_start_combobox.setCurrentIndex(1)
        left_layout.addWidget(self.server_start_combobox)

        test_start_pz_server_button.clicked.connect(self.test_start_pz_server)

        layout.addLayout(left_layout)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

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

        self.console_input = QLineEdit()
        self.console_input.returnPressed.connect(self.send_command)
        console_layout.addWidget(self.console_input)

        server_layout.addLayout(console_layout, stretch=1)

        player_list_layout = QVBoxLayout()
        player_list_label = QLabel("Player List")
        player_list_layout.addWidget(player_list_label)
        self.player_list = QListWidget()
        player_list_layout.addWidget(self.player_list)
        server_layout.addLayout(player_list_layout, stretch=1)

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

        layout.addLayout(side_layout, stretch=1)

        browser = BrowserEngine()
        layout.addWidget(browser, stretch=3)

    def send_command(self):
        command = self.console_input.text()
        self.console.append(f"> {command}")
        self.console_input.clear()

    def start_server(self):
        self.console.append("Starting Server...")

    def save_and_quit(self):
        self.console.append("Saving and Quitting...")

    def terminate_server(self):
        self.console.append("Terminating Server...")

    def install_steamcmd(self):
        self.console.append("Installing SteamCMD...")

    def install_pz_server(self):
        self.console.append("Installing Project Zomboid Dedicated Server...")

    def test_start_pz_server(self):
        server_option = self.server_start_combobox.currentText()
        self.console.append(f"Test starting Project Zomboid Dedicated Server with option: {server_option}")

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
        if self.light_theme_rb.isChecked():
            self.current_theme = 'Light'
        elif self.light_dark_theme_rb.isChecked():
            self.current_theme = 'Light Dark'
        elif self.dark_theme_rb.isChecked():
            self.current_theme == 'Dark'

        self.apply_theme(self.current_theme)

        self.config.set('Settings', 'theme', self.current_theme)
        with open('config.ini', 'w') as configfile:
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
