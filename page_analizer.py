import re
import requests
import logging
from pyquery import PyQuery as pq

logging.basicConfig(level=logging.INFO)


class SteamWorkshopIdentifier:
    def __init__(self):
        pass

    def check_url(self, url):
        logging.info(f"Checking URL: {url}")

        invalid_urls = [
            "https://steamcommunity.com/app/108600/workshop/",
            "https://steamcommunity.com/workshop/browse/?appid=108600",
        ]

        if any(url.startswith(invalid_url) for invalid_url in invalid_urls):
            logging.warning("Invalid workshop browser link.")
            raise ValueError("Invalid workshop browser link.")

        try:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            html_content = response.text
            result = self.identify_page_type(html_content)
            return result
        except Exception as e:
            logging.error(f"Failed to load page: {e}")
            raise ConnectionError(f"Failed to load page: {e}")

    def identify_page_type(self, html_content):
        logging.info("Starting to identify page type.")
        doc = pq(html_content)

        workshop_ids = set()
        mod_ids = set()
        map_folders = set()

        # Извлечение имени мода (заголовка страницы)
        mod_name = doc('div.workshopItemTitle').text().strip()

        logging.info(f"Extracted mod name: {mod_name}")

        # Проверка на modpack
        if doc('a[href*="https://steamcommunity.com/workshop/browse/?section=collections&appid=108600"]').length > 0:
            logging.info("Identified as modpack.")
            return ["Page Type: modpack", f"Mod Name: {mod_name}"]

        # Извлечение текста элементов
        text_elements = doc('body').text().split('\n')
        capture_next = None

        for text in text_elements:
            text = text.strip()
            logging.debug(f"Processing text: {text}")

            if capture_next == "mod_id" and text and not text.startswith(('Workshop ID:', 'Mod ID:', 'Map Folder:')):
                mod_ids.add(text)
                capture_next = None
            elif capture_next == "map_folder" and text and not text.startswith(
                    ('Workshop ID:', 'Mod ID:', 'Map Folder:')):
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

        result = []
        page_type = "map" if map_folders else "mod"
        logging.info(f"Page type identified as: {page_type}")
        result.append(f"Page Type: {page_type}")
        result.append(f"Mod Name: {mod_name}")  # Убедимся, что имя добавляется

        if workshop_ids:
            result.append(f"Workshop ID: {', '.join(sorted(workshop_ids))}")
        if mod_ids:
            result.append(f"Mod ID: {', '.join(sorted(mod_ids))}")
        if map_folders:
            result.append(f"Map Folder: {', '.join(sorted(map_folders))}")

        return result
