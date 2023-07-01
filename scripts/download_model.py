import os
from huggingface_hub import hf_hub_download, snapshot_download


def download_model(repo_id: str, filename:str, cache_dir:str):
    hf_hub_download(repo_id=repo_id, filename=filename, cache_dir=cache_dir)


if __name__ == "__main__":
    repo_id="naver-clova-ix/donut-base-finetuned-cord-v2"
    #download_model(repo_id="naver-clova-ix/donut-base-finetuned-cord-v2", filename="config.json", cache_dir="/Users/slc/huggingface_models/")
    os.environ.setdefault("https_proxy", "socks5://127.0.0.1:2002")
    snapshot_download(repo_id=repo_id)
