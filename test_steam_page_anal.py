import sys
import requests
import logging
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTextEdit
from bs4 import BeautifulSoup, Comment

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class SteamWorkshopIdentifier(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Steam Workshop Identifier")
        self.setGeometry(300, 300, 600, 400)

        self.layout = QVBoxLayout()

        self.url_label = QLabel("Enter the Steam Workshop page URL:")
        self.layout.addWidget(self.url_label)

        self.url_input = QLineEdit()
        self.layout.addWidget(self.url_input)

        self.check_button = QPushButton("Check")
        self.check_button.clicked.connect(self.check_url)
        self.layout.addWidget(self.check_button)

        self.result_label = QLabel("")
        self.layout.addWidget(self.result_label)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.layout.addWidget(self.details_text)

        self.setLayout(self.layout)

    def check_url(self):
        url = self.url_input.text()
        logging.info(f"Checking URL: {url}")

        if "https://steamcommunity.com/workshop/browse/?section=collections&appid=108600" in url:
            logging.warning("Invalid collection link.")
            QMessageBox.warning(self, "Error", "Invalid collection link.")
            return

        try:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = 'cp-1251'  # Set the encoding to cp-1251
            html_content = response.text
            result, details = self.identify_page_type(html_content)
            self.result_label.setText(f"Page Type: {result}")
            self.details_text.setText(details)
        except Exception as e:
            logging.error(f"Failed to load page: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load page: {e}")

    def identify_page_type(self, html_content):
        logging.info("Starting to identify page type.")
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove scripts, styles, and comments
        for element in soup(["script", "style"]):
            logging.debug(f"Removing element: {element.name}")
            element.extract()
        for comment in soup.findAll(string=lambda text: isinstance(text, Comment)):
            logging.debug("Removing comment")
            comment.extract()

        clean_text = soup.get_text(separator="\n")
        logging.debug(f"Clean text: {clean_text[:1000]}...")  # Log the first 100000 characters of the clean text

        if "https://steamcommunity.com/workshop/browse/?section=collections&appid=108600" in clean_text:
            logging.info("Identified as modpack.")
            return "modpack", ""

        workshop_ids = set()
        mod_ids = set()
        map_folders = set()

        logging.debug("Starting to parse text lines.")
        lines = clean_text.split("\n")
        capture_next = None  # Flag to capture the next line

        for line in lines:
            line = line.strip()
            logging.debug(f"Processing line: {line}")

            if capture_next == "workshop_id" and line:
                workshop_ids.add(line)
                logging.debug(f"Captured Workshop ID: {line}")
                capture_next = None
            elif capture_next == "mod_id" and line:
                mod_ids.add(line)
                logging.debug(f"Captured Mod ID: {line}")
                capture_next = None
            elif capture_next == "map_folder" and line:
                map_folders.add(line)
                logging.debug(f"Captured Map Folder: {line}")
                capture_next = None

            if "Workshop ID" in line:
                capture_next = "workshop_id"
            elif "Mod ID" in line:
                capture_next = "mod_id"
            elif "Map Folder" in line:
                capture_next = "map_folder"

        details = ""
        if workshop_ids:
            details += "Workshop ID:\n" + "\n".join(workshop_ids) + "\n"
        if mod_ids:
            details += "Mod ID:\n" + "\n".join(mod_ids) + "\n"
        if map_folders:
            details += "Map Folder:\n" + "\n".join(map_folders) + "\n"

        page_type = "map" if map_folders else "mod"
        logging.info(f"Page type identified as: {page_type}")
        return page_type, details

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SteamWorkshopIdentifier()
    window.show()
    sys.exit(app.exec())
