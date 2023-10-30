import requests
import tempfile
from typing import Dict, Any, Iterator
from bs4 import BeautifulSoup
from kubechat.source.base import Source, RemoteDocument, LocalDocument, CustomSourceInitializationError


def fetch_and_clean_text(url: str, name: str):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    clean_text = soup.get_text(separator=' ')
    prefix = name.strip("/").replace("/", "--")
    return clean_text, prefix


def download_web_text_to_temp_file(url, name):
    web_text, prefix = fetch_and_clean_text(url, name)
    temp_file = tempfile.NamedTemporaryFile(
        prefix=prefix,
        delete=False,
        suffix=".txt",
    )
    temp_file.write(web_text.encode("utf-8"))
    temp_file.close()
    return temp_file


class URLSource(Source):
    def __init__(self, ctx: Dict[str, Any]):
        super().__init__(ctx)
        self.url = ctx["url"]
        if self.url == "":
            raise CustomSourceInitializationError(f"None URL")

    def sync_enabled(self):
        return True

    def scan_documents(self) -> Iterator[RemoteDocument]:
        return iter([])

    def prepare_document(self, name: str, metadata: Dict[str, Any]) -> LocalDocument:
        url = self.url
        temp_file_path = download_web_text_to_temp_file(
            url, name
        ).name
        metadata["url"] = url
        return LocalDocument(name=name, path=temp_file_path, metadata=metadata)
