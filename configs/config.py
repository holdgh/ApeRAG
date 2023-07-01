#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import List

from auto_gpt_plugin_template import AutoGPTPluginTemplate

from utils.singleton import Singleton
from common.sql_database import Database


class Config(metaclass=Singleton):
    """Configuration class to store the state of bools for different scripts access"""

    def __init__(self) -> None:
        """Initialize the Config class"""

        # This is a proxy server, just for test_py.  we will remove this later.
        self.proxy_api_key = os.getenv("PROXY_API_KEY")
        self.proxy_server_url = os.getenv("PROXY_SERVER_URL")

        ### LLM Model Service Configuration
        self.LLM_MODEL = os.getenv("LLM_MODEL", "vicuna-13b")
        self.LIMIT_MODEL_CONCURRENCY = int(os.getenv("LIMIT_MODEL_CONCURRENCY", 5))
        self.MAX_POSITION_EMBEDDINGS = int(os.getenv("MAX_POSITION_EMBEDDINGS", 4096))
        self.MODEL_PORT = os.getenv("MODEL_PORT", 8000)
        self.MODEL_SERVER = os.getenv(
            "MODEL_SERVER", "http://127.0.0.1" + ":" + str(self.MODEL_PORT)
        )

        # QLoRA
        self.QLoRA = os.getenv("QUANTIZE_QLORA", "True")
