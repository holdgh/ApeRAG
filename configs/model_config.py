#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os

import nltk
import torch

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_PATH = os.path.join(ROOT_PATH, "resources")
VECTORE_PATH = os.path.join(RESOURCES_PATH, "vector_store")
MODEL_PATH = os.path.join(RESOURCES_PATH, "models")
LOGDIR = os.path.join(ROOT_PATH, "logs")
DATASETS_DIR = os.path.join(RESOURCES_PATH, "datasets")
DATA_DIR = os.path.join(RESOURCES_PATH, "data")
nltk.data.path = [os.path.join(RESOURCES_PATH, "nltk_data")] + nltk.data.path
PLUGINS_DIR = os.path.join(ROOT_PATH, "plugins")

current_directory = os.getcwd()

new_directory = RESOURCES_PATH
os.chdir(new_directory)

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)
LLM_MODEL_CONFIG = {
    "flan-t5-base": os.path.join(MODEL_PATH, "flan-t5-base"),
    "vicuna-13b": os.path.join(MODEL_PATH, "vicuna-13b"),
    "vicuna-7b": os.path.join(MODEL_PATH, "vicuna-7b"),
    "text2vec": os.path.join(MODEL_PATH, "text2vec-large-chinese"),
    "sentence-transforms": os.path.join(MODEL_PATH, "all-MiniLM-L6-v2"),
    "codegen2-1b": os.path.join(MODEL_PATH, "codegen2-1B"),
    "codet5p-2b": os.path.join(MODEL_PATH, "codet5p-2b"),
    "chatglm-6b-int4": os.path.join(MODEL_PATH, "chatglm-6b-int4"),
    "chatglm-6b": os.path.join(MODEL_PATH, "chatglm-6b"),
    "text2vec-base": os.path.join(MODEL_PATH, "text2vec-base-chinese"),
    "guanaco-33b-merged": os.path.join(MODEL_PATH, "guanaco-33b-merged"),
    "falcon-40b": os.path.join(MODEL_PATH, "falcon-40b"),
    "gorilla-7b": os.path.join(MODEL_PATH, "gorilla-7b"),
    # TODO Support baichuan-7b
    # "baichuan-7b" : os.path.join(MODEL_PATH, "baichuan-7b"),
    "gptj-6b": os.path.join(MODEL_PATH, "ggml-gpt4all-j-v1.3-groovy.bin"),
    "gptl-13b": os.path.join(MODEL_PATH, "ggml-gpt4all-l13b-snoozy.bin"),
    "proxyllm": "proxyllm",
}

# Load model config
ISLOAD_8BIT = True
ISDEBUG = False

VECTOR_SEARCH_TOP_K = 10
VS_ROOT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vs_store")
KNOWLEDGE_UPLOAD_ROOT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data"
)
KNOWLEDGE_CHUNK_SPLIT_SIZE = 100
