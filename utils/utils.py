#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import logging
import logging.handlers
import os
import sys

import torch

from configs.model_config import LOGDIR

server_error_msg = (
    "**NETWORK ERROR DUE TO HIGH TRAFFIC. PLEASE REGENERATE OR REFRESH THIS PAGE.**"
)

handler = None


def get_gpu_memory(max_gpus=None):
    gpu_memory = []
    num_gpus = (
        torch.cuda.device_count()
        if max_gpus is None
        else min(max_gpus, torch.cuda.device_count())
    )

    for gpu_id in range(num_gpus):
        with torch.cuda.device(gpu_id):
            device = torch.cuda.current_device()
            gpu_properties = torch.cuda.get_device_properties(device)
            total_memory = gpu_properties.total_memory / (1024 ** 3)
            allocated_memory = torch.cuda.memory_allocated() / (1024 ** 3)
            available_memory = total_memory - allocated_memory
            gpu_memory.append(available_memory)
    return gpu_memory


def build_logger(logger_name, logger_filename):
    global handler

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set the format of root handlers
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, encoding="utf-8")
    logging.getLogger().handlers[0].setFormatter(formatter)

    # Redirect stdout and stderr to loggers
    stdout_logger = logging.getLogger("stdout")
    stdout_logger.setLevel(logging.INFO)
    sl = StreamToLogger(stdout_logger, logging.INFO)
    sys.stdout = sl

    stderr_logger = logging.getLogger("stderr")
    stderr_logger.setLevel(logging.ERROR)
    sl = StreamToLogger(stderr_logger, logging.ERROR)
    sys.stderr = sl

    # Get logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Add a file handler for all loggers
    if handler is None:
        os.makedirs(LOGDIR, exist_ok=True)
        filename = os.path.join(LOGDIR, logger_filename)
        handler = logging.handlers.TimedRotatingFileHandler(
            filename, when="D", utc=True
        )
        handler.setFormatter(formatter)

        for name, item in logging.root.manager.loggerDict.items():
            if isinstance(item, logging.Logger):
                item.addHandler(handler)

    return logger


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.terminal = sys.stdout
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ""

    def __getattr__(self, attr):
        return getattr(self.terminal, attr)

    def write(self, buf):
        temp_linebuf = self.linebuf + buf
        self.linebuf = ""
        for line in temp_linebuf.splitlines(True):
            # From the io.TextIOWrapper docs:
            #   On output, if newline is None, any '\n' characters written
            #   are translated to the system default line separator.
            # By default sys.stdout.write() expects '\n' newlines and then
            # translates them so this is still cross platform.
            if line[-1] == "\n":
                encoded_message = line.encode("utf-8", "ignore").decode("utf-8")
                self.logger.log(self.log_level, encoded_message.rstrip())
            else:
                self.linebuf += line

    def flush(self):
        if self.linebuf != "":
            encoded_message = self.linebuf.encode("utf-8", "ignore").decode("utf-8")
            self.logger.log(self.log_level, encoded_message.rstrip())
        self.linebuf = ""


def disable_torch_init():
    """
    Disable the redundant torch default initialization to accelerate model creation.
    """
    import torch

    setattr(torch.nn.Linear, "reset_parameters", lambda self: None)
    setattr(torch.nn.LayerNorm, "reset_parameters", lambda self: None)


def pretty_print_semaphore(semaphore):
    if semaphore is None:
        return "None"
    return f"Semaphore(value={semaphore._value}, locked={semaphore.locked()})"


class Stacks:
    """
    An array of stacks for local document embedding
    the array index is the docx title level
    the every stack store the level contents
    """

    def __init__(self):
        self.stacks = [[]]  # [] is a placeholder

    def push(self, level: int, value: str):
        """
        push the string to the stack at level
        :param level: the level of the stack we want to push
        :param value: content of the string
        """
        while level >= len(self.stacks):
            self.stacks.append([])
        self.stacks[level].append(value)

    def pop(self, level: int):
        """
        pop from the stack at level
        :param level: the level of the stack we want to pop
        :return: the pop elelment
        """
        if level >= len(self.stacks):
            return None
        if len(self.stacks[level]) == 0:
            return None
        return self.stacks[level].pop()

    def package_content(self, level: int):
        """
        package the stack contents to a trunk from  0 ~ level
        :param level: the deepest level to package
        :return: content string
        """
        res = ""
        for i in range(0, level + 1):
            for j in range(0, len(self.stacks[i])):
                if j == 0:
                    res += "\n"      # add "\n" for different level title
                res += self.stacks[i][j]

        return res

    def count_contents(self, level: int):
        """
        count the contexts for level
        :param level: the stack level we want to count
        :return: the total length of content at level
        """
        res = 0
        for i in range(0, len(self.stacks[level])):
            res += len(self.stacks[level][i])
        return res

    def remove(self, level):
        """
        remove the stacks contents from level to the deepest level
        :param level: begin level
        """
        for i in range(level, len(self.stacks)):
            while len(self.stacks[i]) > 0:
                self.pop(i)

    def get_title(self, level):
        """
        get the title
        :param level: the level of the title
        :return: the content of title
        """
        return self.stacks[level][0]
