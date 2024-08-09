# browser_engine.py

from PySide6.QtWebEngineWidgets import QWebEngineView

class BrowserEngine(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.load("https://steamcommunity.com/app/108600/workshop/")

    def get_current_url(self):
        return self.url().toString()
