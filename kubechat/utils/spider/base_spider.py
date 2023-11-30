import requests

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from kubechat.utils.spider.zhihu import get_zhihu
from kubechat.utils.spider.stackoverflow import get_stackoverflow


def get_default(url: str):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    clean_text = soup.get_text(separator=' ')
    return clean_text


def url_selector(url, name):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    prefix = name.strip("/").replace("/", "--")
    if "zhihu" in domain:
        return get_zhihu(url), prefix
    if "stackoverflow" in domain:
        return get_stackoverflow(url), prefix
    else:
        return get_default(url), prefix
