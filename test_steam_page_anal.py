import re
import sys
import requests
import logging
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTextEdit
from pyquery import PyQuery as pq

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

        invalid_urls = [
            "https://steamcommunity.com/app/108600/workshop/",
            "https://steamcommunity.com/workshop/browse/?appid=108600",
        ]

        if any(url.startswith(invalid_url) for invalid_url in invalid_urls):
            logging.warning("Invalid workshop browser link.")
            QMessageBox.warning(self, "Error", "Invalid workshop browser link.")
            return

        try:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            html_content = response.text
            result, details = self.identify_page_type(html_content)
            self.result_label.setText(f"Page Type: {result}")
            self.details_text.setText(details)
        except Exception as e:
            logging.error(f"Failed to load page: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load page: {e}")

    def identify_page_type(self, html_content):
        logging.info("Starting to identify page type.")
        doc = pq(html_content)

        workshop_ids = set()
        mod_ids = set()
        map_folders = set()

        # Check if the page is a modpack
        if doc('a[href*="https://steamcommunity.com/workshop/browse/?section=collections&appid=108600"]').length > 0:
            logging.info("Identified as modpack.")
            return "modpack", ""

        # Extract text from elements
        text_elements = doc('body').text().split('\n')
        capture_next = None

        for text in text_elements:
            text = text.strip()
            logging.debug(f"Processing text: {text}")

            # Skip unwanted text
            if "Popular Discussions View All" in text or "View All" in text or "Discussions" in text:
                continue

            if capture_next == "mod_id" and text and not text.startswith(('Workshop ID:', 'Mod ID:', 'Map Folder:')):
                mod_ids.add(text)
                capture_next = None
            elif capture_next == "map_folder" and text and not text.startswith(('Workshop ID:', 'Mod ID:', 'Map Folder:')):
                map_folders.add(text)
                capture_next = None

            if "Workshop ID" in text:
                match = re.search(r'Workshop ID:?\s*(\d+)', text, re.IGNORECASE)
                if match:
                    workshop_ids.add(match.group(1).strip())
            elif "Mod ID" in text:
                capture_next = "mod_id"
                match = re.search(r'Mod ID:?\s*([\w\d\s_-]+)', text, re.IGNORECASE)
                if match:
                    mod_ids.add(match.group(1).strip())
                    capture_next = None
            elif "Map Folder" in text:
                capture_next = "map_folder"
                match = re.search(r'Map Folder:?\s*([\w\d\s_-]+)', text, re.IGNORECASE)
                if match:
                    map_folders.add(match.group(1).strip())
                    capture_next = None

        details = ""
        if workshop_ids:
            details += "Workshop ID:\n" + "\n".join(sorted(workshop_ids)) + "\n"
        if mod_ids:
            details += "Mod ID:\n" + "\n".join(sorted(mod_ids)) + "\n"
        if map_folders:
            details += "Map Folder:\n" + "\n".join(sorted(map_folders)) + "\n"

        page_type = "map" if map_folders else "mod"
        logging.info(f"Page type identified as: {page_type}")
        return page_type, details

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SteamWorkshopIdentifier()
    window.show()
    sys.exit(app.exec())
