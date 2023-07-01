import os
from huggingface_hub import hf_hub_download, snapshot_download


def download_model(repo_id: str, filename:str, cache_dir:str):
    hf_hub_download(repo_id=repo_id, filename=filename, cache_dir=cache_dir)


if __name__ == "__main__":

    repo_is = [
        "nlpconnect/vit-gpt2-image-captioning",
        "Salesforce/blip-image-captioning-base",
        "hustvl/yolos-tiny",
    ]
    os.environ.setdefault("https_proxy", "socks5://127.0.0.1:2002")

    for repo_id in repo_is:
        print("repo:", repo_id)
        snapshot_download(repo_id=repo_id)
