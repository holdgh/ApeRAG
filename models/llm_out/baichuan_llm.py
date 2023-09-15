#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import torch


@torch.inference_mode()
def baichuan_generate_stream(
    model, tokenizer, params, device, context_len=4096, stream_interval=2
):
    prompt = params["prompt"]
    temperature = params.get("temperature", 0.001)
    model.generation_config.temperature = temperature

    messages = [{"role": "user", "content": prompt}]
    for response in model.chat(tokenizer, messages, stream=True):
        yield response
