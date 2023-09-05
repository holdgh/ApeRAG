import os

from huggingface_hub import hf_hub_download, snapshot_download
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


def download_model(repo_id: str, filename: str, cache_dir: str):
    hf_hub_download(repo_id=repo_id, filename=filename, cache_dir=cache_dir)


if __name__ == "__main__":
    repo_is = [
        "BAAI/bge-large-zh",
    ]
    os.environ.setdefault("https_proxy", "socks5://127.0.0.1:34001")

    from text2vec import SentenceModel
    model_name = "GanymedeNil/text2vec-large-chinese"
    model = SentenceModel(model_name)
    # tokenizer = AutoTokenizer.from_pretrained(model_name)
    # model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    # for repo_id in repo_is:
    #     print("repo:", repo_id)
    #     snapshot_download(repo_id=repo_id)
