import requests
import os
import zipfile


def download_steamcmd(download_path):
    url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
    local_zip_path = os.path.join(download_path, "steamcmd.zip")

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_zip_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return local_zip_path


def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
