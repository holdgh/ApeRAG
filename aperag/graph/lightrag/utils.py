from __future__ import annotations

import asyncio
import csv
import html
import json
import logging
import logging.handlers
import os
import re
import weakref
from dataclasses import dataclass
from functools import wraps
from hashlib import md5
from typing import TYPE_CHECKING, Any, Callable, List, Protocol

import numpy as np
from dotenv import load_dotenv

from aperag.graph.lightrag.constants import (
    DEFAULT_LOG_BACKUP_COUNT,
    DEFAULT_LOG_FILENAME,
    DEFAULT_LOG_MAX_BYTES,
)
from aperag.graph.lightrag.prompt import PROMPTS


def get_env_value(
    env_key: str, default: any, value_type: type = str, special_none: bool = False
) -> any:
    """
    Get value from environment variable with type conversion

    Args:
        env_key (str): Environment variable key
        default (any): Default value if env variable is not set
        value_type (type): Type to convert the value to
        special_none (bool): If True, return None when value is "None"

    Returns:
        any: Converted value from environment or default
    """
    value = os.getenv(env_key)
    if value is None:
        return default

    # Handle special case for "None" string
    if special_none and value == "None":
        return None

    if value_type is bool:
        return value.lower() in ("true", "1", "yes", "t", "on")
    try:
        return value_type(value)
    except (ValueError, TypeError):
        return default


# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from aperag.graph.lightrag.base import BaseKVStorage

# use the .env that is inside the current folder
# allows to use different .env file for each lightrag instance
# the OS environment variables take precedence over the .env file
load_dotenv(dotenv_path=".env", override=False)

VERBOSE_DEBUG = os.getenv("VERBOSE", "false").lower() == "true"


def verbose_debug(msg: str, *args, **kwargs):
    """Function for outputting detailed debug information.
    When VERBOSE_DEBUG=True, outputs the complete message.
    When VERBOSE_DEBUG=False, outputs only the first 50 characters.

    Args:
        msg: The message format string
        *args: Arguments to be formatted into the message
        **kwargs: Keyword arguments passed to logger.debug()
    """
    if VERBOSE_DEBUG:
        logger.debug(msg, *args, **kwargs)
    else:
        # Format the message with args first
        if args:
            formatted_msg = msg % args
        else:
            formatted_msg = msg
        # Then truncate the formatted message
        truncated_msg = (
            formatted_msg[:100] + "..." if len(formatted_msg) > 100 else formatted_msg
        )
        logger.debug(truncated_msg, **kwargs)


def set_verbose_debug(enabled: bool):
    """Enable or disable verbose debug output"""
    global VERBOSE_DEBUG
    VERBOSE_DEBUG = enabled


# Initialize logger
logger = logging.getLogger("lightrag")
logger.propagate = False  # prevent log message send to root loggger
# Let the main application configure the handlers
logger.setLevel(logging.INFO)

# Set httpx logging level to WARNING
logging.getLogger("httpx").setLevel(logging.WARNING)


class LightragPathFilter(logging.Filter):
    """Filter for lightrag logger to filter out frequent path access logs"""

    def __init__(self):
        super().__init__()
        # Define paths to be filtered
        self.filtered_paths = [
            "/documents",
            "/health",
            "/webui/",
            "/documents/processing_status",
            "/documents/stats",
        ]
        # self.filtered_paths = ["/health", "/webui/"]

    def filter(self, record):
        try:
            # Check if record has the required attributes for an access log
            if not hasattr(record, "args") or not isinstance(record.args, tuple):
                return True
            if len(record.args) < 5:
                return True

            # Extract method, path and status from the record args
            method = record.args[1]
            path = record.args[2]
            status = record.args[4]

            # Filter out successful GET requests to filtered paths
            if (
                method == "GET"
                and (status == 200 or status == 304)
                and path in self.filtered_paths
            ):
                return False

            return True
        except Exception:
            # In case of any error, let the message through
            return True


def setup_logger(
    logger_name: str,
    level: str = "INFO",
    add_filter: bool = False,
    log_file_path: str | None = None,
    enable_file_logging: bool = True,
):
    """Set up a logger with console and optionally file handlers

    Args:
        logger_name: Name of the logger to set up
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        add_filter: Whether to add LightragPathFilter to the logger
        log_file_path: Path to the log file. If None and file logging is enabled, defaults to lightrag.log in LOG_DIR or cwd
        enable_file_logging: Whether to enable logging to a file (defaults to True)
    """
    # Configure formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    simple_formatter = logging.Formatter("%(levelname)s: %(message)s")

    logger_instance = logging.getLogger(logger_name)
    logger_instance.setLevel(level)
    logger_instance.handlers = []  # Clear existing handlers
    logger_instance.propagate = False

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(level)
    logger_instance.addHandler(console_handler)

    # Add file handler by default unless explicitly disabled
    if enable_file_logging:
        # Get log file path
        if log_file_path is None:
            log_dir = os.getenv("LOG_DIR", os.getcwd())
            log_file_path = os.path.abspath(os.path.join(log_dir, DEFAULT_LOG_FILENAME))

        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        # Get log file max size and backup count from environment variables
        log_max_bytes = get_env_value("LOG_MAX_BYTES", DEFAULT_LOG_MAX_BYTES, int)
        log_backup_count = get_env_value(
            "LOG_BACKUP_COUNT", DEFAULT_LOG_BACKUP_COUNT, int
        )

        try:
            # Add file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file_path,
                maxBytes=log_max_bytes,
                backupCount=log_backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(detailed_formatter)
            file_handler.setLevel(level)
            logger_instance.addHandler(file_handler)
        except PermissionError as e:
            logger.warning(f"Could not create log file at {log_file_path}: {str(e)}")
            logger.warning("Continuing with console logging only")

    # Add path filter if requested
    if add_filter:
        path_filter = LightragPathFilter()
        logger_instance.addFilter(path_filter)


class UnlimitedSemaphore:
    """A context manager that allows unlimited access."""

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc, tb):
        pass


@dataclass
class EmbeddingFunc:
    embedding_dim: int
    max_token_size: int
    func: callable
    # concurrent_limit: int = 16

    async def __call__(self, *args, **kwargs) -> np.ndarray:
        return await self.func(*args, **kwargs)


def locate_json_string_body_from_string(content: str) -> str | None:
    """Locate the JSON string body from a string"""
    try:
        maybe_json_str = re.search(r"{.*}", content, re.DOTALL)
        if maybe_json_str is not None:
            maybe_json_str = maybe_json_str.group(0)
            maybe_json_str = maybe_json_str.replace("\\n", "")
            maybe_json_str = maybe_json_str.replace("\n", "")
            maybe_json_str = maybe_json_str.replace("'", '"')
            # json.loads(maybe_json_str) # don't check here, cannot validate schema after all
            return maybe_json_str
    except Exception:
        pass
        # try:
        #     content = (
        #         content.replace(kw_prompt[:-1], "")
        #         .replace("user", "")
        #         .replace("model", "")
        #         .strip()
        #     )
        #     maybe_json_str = "{" + content.split("{")[1].split("}")[0] + "}"
        #     json.loads(maybe_json_str)

        return None


def convert_response_to_json(response: str) -> dict[str, Any]:
    json_str = locate_json_string_body_from_string(response)
    assert json_str is not None, f"Unable to parse JSON from response: {response}"
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {json_str}")
        raise e from None


def compute_args_hash(*args: Any, cache_type: str | None = None) -> str:
    """Compute a hash for the given arguments.
    Args:
        *args: Arguments to hash
        cache_type: Type of cache (e.g., 'keywords', 'query', 'extract')
    Returns:
        str: Hash string
    """
    import hashlib

    # Convert all arguments to strings and join them
    args_str = "".join([str(arg) for arg in args])
    if cache_type:
        args_str = f"{cache_type}:{args_str}"

    # Compute MD5 hash
    return hashlib.md5(args_str.encode()).hexdigest()


def compute_mdhash_id(content: str, prefix: str = "") -> str:
    """
    Compute a unique ID for a given content string.

    The ID is a combination of the given prefix and the MD5 hash of the content string.
    """
    return prefix + md5(content.encode()).hexdigest()


# Custom exception class
class QueueFullError(Exception):
    """Raised when the queue is full and the wait times out"""

    pass


class TokenizerInterface(Protocol):
    """
    Defines the interface for a tokenizer, requiring encode and decode methods.
    """

    def encode(self, content: str) -> List[int]:
        """Encodes a string into a list of tokens."""
        ...

    def decode(self, tokens: List[int]) -> str:
        """Decodes a list of tokens into a string."""
        ...


class Tokenizer:
    """
    A wrapper around a tokenizer to provide a consistent interface for encoding and decoding.
    """

    def __init__(self, model_name: str, tokenizer: TokenizerInterface):
        """
        Initializes the Tokenizer with a tokenizer model name and a tokenizer instance.

        Args:
            model_name: The associated model name for the tokenizer.
            tokenizer: An instance of a class implementing the TokenizerInterface.
        """
        self.model_name: str = model_name
        self.tokenizer: TokenizerInterface = tokenizer

    def encode(self, content: str) -> List[int]:
        """
        Encodes a string into a list of tokens using the underlying tokenizer.

        Args:
            content: The string to encode.

        Returns:
            A list of integer tokens.
        """
        return self.tokenizer.encode(content)

    def decode(self, tokens: List[int]) -> str:
        """
        Decodes a list of tokens into a string using the underlying tokenizer.

        Args:
            tokens: A list of integer tokens to decode.

        Returns:
            The decoded string.
        """
        return self.tokenizer.decode(tokens)


class TiktokenTokenizer(Tokenizer):
    """
    A Tokenizer implementation using the tiktoken library.
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        Initializes the TiktokenTokenizer with a specified model name.

        Args:
            model_name: The model name for the tiktoken tokenizer to use.  Defaults to "gpt-4o-mini".

        Raises:
            ImportError: If tiktoken is not installed.
            ValueError: If the model_name is invalid.
        """
        try:
            import tiktoken
        except ImportError:
            raise ImportError(
                "tiktoken is not installed. Please install it with `pip install tiktoken` or define custom `tokenizer_func`."
            )

        try:
            tokenizer = tiktoken.encoding_for_model(model_name)
            super().__init__(model_name=model_name, tokenizer=tokenizer)
        except KeyError:
            raise ValueError(f"Invalid model_name: {model_name}.")


def pack_user_ass_to_openai_messages(*args: str):
    roles = ["user", "assistant"]
    return [
        {"role": roles[i % 2], "content": content} for i, content in enumerate(args)
    ]


def split_string_by_multi_markers(content: str, markers: list[str]) -> list[str]:
    """Split a string by multiple markers"""
    if not markers:
        return [content]
    content = content if content is not None else ""
    results = re.split("|".join(re.escape(marker) for marker in markers), content)
    return [r.strip() for r in results if r.strip()]


# Refer the utils functions of the official GraphRAG implementation:
# https://github.com/microsoft/graphrag
def clean_str(input: Any) -> str:
    """Clean an input string by removing HTML escapes, control characters, and other unwanted characters."""
    # If we get non-string input, just give it back
    if not isinstance(input, str):
        return input

    result = html.unescape(input.strip())
    # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", result)


def is_float_regex(value: str) -> bool:
    return bool(re.match(r"^[-+]?[0-9]*\.?[0-9]+$", value))


def truncate_list_by_token_size(
    list_data: list[Any],
    key: Callable[[Any], str],
    max_token_size: int,
    tokenizer: Tokenizer,
) -> list[int]:
    """Truncate a list of data by token size"""
    if max_token_size <= 0:
        return []
    tokens = 0
    for i, data in enumerate(list_data):
        tokens += len(tokenizer.encode(key(data)))
        if tokens > max_token_size:
            return list_data[:i]
    return list_data


def process_combine_contexts(*context_lists):
    """
    Combine multiple context lists and remove duplicate content

    Args:
        *context_lists: Any number of context lists

    Returns:
        Combined context list with duplicates removed
    """
    seen_content = {}
    combined_data = []

    # Iterate through all input context lists
    for context_list in context_lists:
        if not context_list:  # Skip empty lists
            continue
        for item in context_list:
            content_dict = {k: v for k, v in item.items() if k != "id"}
            content_key = tuple(sorted(content_dict.items()))
            if content_key not in seen_content:
                seen_content[content_key] = item
                combined_data.append(item)

    # Reassign IDs
    for i, item in enumerate(combined_data):
        item["id"] = str(i + 1)

    return combined_data


async def get_best_cached_response(
    hashing_kv,
    current_embedding,
    similarity_threshold=0.95,
    mode="default",
    use_llm_check=False,
    llm_func=None,
    original_prompt=None,
    cache_type=None,
) -> str | None:
    logger.debug(
        f"get_best_cached_response:  mode={mode} cache_type={cache_type} use_llm_check={use_llm_check}"
    )
    mode_cache = await hashing_kv.get_by_id(mode)
    if not mode_cache:
        return None

    best_similarity = -1
    best_response = None
    best_prompt = None
    best_cache_id = None

    # Only iterate through cache entries for this mode
    for cache_id, cache_data in mode_cache.items():
        # Skip if cache_type doesn't match
        if cache_type and cache_data.get("cache_type") != cache_type:
            continue

        # Check if cache data is valid
        if cache_data["embedding"] is None:
            continue

        try:
            # Safely convert cached embedding
            cached_quantized = np.frombuffer(
                bytes.fromhex(cache_data["embedding"]), dtype=np.uint8
            ).reshape(cache_data["embedding_shape"])

            # Ensure min_val and max_val are valid float values
            embedding_min = cache_data.get("embedding_min")
            embedding_max = cache_data.get("embedding_max")

            if (
                embedding_min is None
                or embedding_max is None
                or embedding_min >= embedding_max
            ):
                logger.warning(
                    f"Invalid embedding min/max values: min={embedding_min}, max={embedding_max}"
                )
                continue

            cached_embedding = dequantize_embedding(
                cached_quantized,
                embedding_min,
                embedding_max,
            )
        except Exception as e:
            logger.warning(f"Error processing cached embedding: {str(e)}")
            continue

        similarity = cosine_similarity(current_embedding, cached_embedding)
        if similarity > best_similarity:
            best_similarity = similarity
            best_response = cache_data["return"]
            best_prompt = cache_data["original_prompt"]
            best_cache_id = cache_id

    if best_similarity > similarity_threshold:
        # If LLM check is enabled and all required parameters are provided
        if (
            use_llm_check
            and llm_func
            and original_prompt
            and best_prompt
            and best_response is not None
        ):
            compare_prompt = PROMPTS["similarity_check"].format(
                original_prompt=original_prompt, cached_prompt=best_prompt
            )

            try:
                llm_result = await llm_func(compare_prompt)
                llm_result = llm_result.strip()
                llm_similarity = float(llm_result)

                # Replace vector similarity with LLM similarity score
                best_similarity = llm_similarity
                if best_similarity < similarity_threshold:
                    log_data = {
                        "event": "cache_rejected_by_llm",
                        "type": cache_type,
                        "mode": mode,
                        "original_question": original_prompt[:100] + "..."
                        if len(original_prompt) > 100
                        else original_prompt,
                        "cached_question": best_prompt[:100] + "..."
                        if len(best_prompt) > 100
                        else best_prompt,
                        "similarity_score": round(best_similarity, 4),
                        "threshold": similarity_threshold,
                    }
                    logger.debug(json.dumps(log_data, ensure_ascii=False))
                    logger.info(f"Cache rejected by LLM(mode:{mode} tpye:{cache_type})")
                    return None
            except Exception as e:  # Catch all possible exceptions
                logger.warning(f"LLM similarity check failed: {e}")
                return None  # Return None directly when LLM check fails

        prompt_display = (
            best_prompt[:50] + "..." if len(best_prompt) > 50 else best_prompt
        )
        log_data = {
            "event": "cache_hit",
            "type": cache_type,
            "mode": mode,
            "similarity": round(best_similarity, 4),
            "cache_id": best_cache_id,
            "original_prompt": prompt_display,
        }
        logger.debug(json.dumps(log_data, ensure_ascii=False))
        return best_response
    return None


def cosine_similarity(v1, v2):
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    return dot_product / (norm1 * norm2)


def quantize_embedding(embedding: np.ndarray | list[float], bits: int = 8) -> tuple:
    """Quantize embedding to specified bits"""
    # Convert list to numpy array if needed
    if isinstance(embedding, list):
        embedding = np.array(embedding)

    # Calculate min/max values for reconstruction
    min_val = embedding.min()
    max_val = embedding.max()

    if min_val == max_val:
        # handle constant vector
        quantized = np.zeros_like(embedding, dtype=np.uint8)
        return quantized, min_val, max_val

    # Quantize to 0-255 range
    scale = (2**bits - 1) / (max_val - min_val)
    quantized = np.round((embedding - min_val) * scale).astype(np.uint8)

    return quantized, min_val, max_val


def dequantize_embedding(
    quantized: np.ndarray, min_val: float, max_val: float, bits=8
) -> np.ndarray:
    """Restore quantized embedding"""
    if min_val == max_val:
        # handle constant vector
        return np.full_like(quantized, min_val, dtype=np.float32)

    scale = (max_val - min_val) / (2**bits - 1)
    return (quantized * scale + min_val).astype(np.float32)


def get_conversation_turns(
    conversation_history: list[dict[str, Any]], num_turns: int
) -> str:
    """
    Process conversation history to get the specified number of complete turns.

    Args:
        conversation_history: List of conversation messages in chronological order
        num_turns: Number of complete turns to include

    Returns:
        Formatted string of the conversation history
    """
    # Check if num_turns is valid
    if num_turns <= 0:
        return ""

    # Group messages into turns
    turns: list[list[dict[str, Any]]] = []
    messages: list[dict[str, Any]] = []

    # First, filter out keyword extraction messages
    for msg in conversation_history:
        if msg["role"] == "assistant" and (
            msg["content"].startswith('{ "high_level_keywords"')
            or msg["content"].startswith("{'high_level_keywords'")
        ):
            continue
        messages.append(msg)

    # Then process messages in chronological order
    i = 0
    while i < len(messages) - 1:
        msg1 = messages[i]
        msg2 = messages[i + 1]

        # Check if we have a user-assistant or assistant-user pair
        if (msg1["role"] == "user" and msg2["role"] == "assistant") or (
            msg1["role"] == "assistant" and msg2["role"] == "user"
        ):
            # Always put user message first in the turn
            if msg1["role"] == "assistant":
                turn = [msg2, msg1]  # user, assistant
            else:
                turn = [msg1, msg2]  # user, assistant
            turns.append(turn)
        i += 2

    # Keep only the most recent num_turns
    if len(turns) > num_turns:
        turns = turns[-num_turns:]

    # Format the turns into a string
    formatted_turns: list[str] = []
    for turn in turns:
        formatted_turns.extend(
            [f"user: {turn[0]['content']}", f"assistant: {turn[1]['content']}"]
        )

    return "\n".join(formatted_turns)


def always_get_an_event_loop() -> asyncio.AbstractEventLoop:
    """
    Ensure that there is always an event loop available.

    This function tries to get the current event loop. If the current event loop is closed or does not exist,
    it creates a new event loop and sets it as the current event loop.

    Returns:
        asyncio.AbstractEventLoop: The current or newly created event loop.
    """
    try:
        # Try to get the current event loop
        current_loop = asyncio.get_event_loop()
        if current_loop.is_closed():
            raise RuntimeError("Event loop is closed.")
        return current_loop

    except RuntimeError:
        # If no event loop exists or it is closed, create a new one
        logger.info("Creating a new event loop in main thread.")
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        return new_loop

def lazy_external_import(module_name: str, class_name: str) -> Callable[..., Any]:
    """Lazily import a class from an external module based on the package of the caller."""
    # Get the caller's module and package
    import inspect

    caller_frame = inspect.currentframe().f_back
    module = inspect.getmodule(caller_frame)
    package = module.__package__ if module else None

    def import_class(*args: Any, **kwargs: Any):
        import importlib

        module = importlib.import_module(module_name, package=package)
        cls = getattr(module, class_name)
        return cls(*args, **kwargs)

    return import_class


def get_content_summary(content: str, max_length: int = 250) -> str:
    """Get summary of document content

    Args:
        content: Original document content
        max_length: Maximum length of summary

    Returns:
        Truncated content with ellipsis if needed
    """
    content = content.strip()
    if len(content) <= max_length:
        return content
    return content[:max_length] + "..."


def normalize_extracted_info(name: str, is_entity=False) -> str:
    """Normalize entity/relation names and description with the following rules:
    1. Remove spaces between Chinese characters
    2. Remove spaces between Chinese characters and English letters/numbers
    3. Preserve spaces within English text and numbers
    4. Replace Chinese parentheses with English parentheses
    5. Replace Chinese dash with English dash
    6. Remove English quotation marks from the beginning and end of the text
    7. Remove English quotation marks in and around chinese
    8. Remove Chinese quotation marks

    Args:
        name: Entity name to normalize

    Returns:
        Normalized entity name
    """
    # Replace Chinese parentheses with English parentheses
    name = name.replace("（", "(").replace("）", ")")

    # Replace Chinese dash with English dash
    name = name.replace("—", "-").replace("－", "-")

    # Use regex to remove spaces between Chinese characters
    # Regex explanation:
    # (?<=[\u4e00-\u9fa5]): Positive lookbehind for Chinese character
    # \s+: One or more whitespace characters
    # (?=[\u4e00-\u9fa5]): Positive lookahead for Chinese character
    name = re.sub(r"(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])", "", name)

    # Remove spaces between Chinese and English/numbers/symbols
    name = re.sub(
        r"(?<=[\u4e00-\u9fa5])\s+(?=[a-zA-Z0-9\(\)\[\]@#$%!&\*\-=+_])", "", name
    )
    name = re.sub(
        r"(?<=[a-zA-Z0-9\(\)\[\]@#$%!&\*\-=+_])\s+(?=[\u4e00-\u9fa5])", "", name
    )

    # Remove English quotation marks from the beginning and end
    if len(name) >= 2 and name.startswith('"') and name.endswith('"'):
        name = name[1:-1]
    if len(name) >= 2 and name.startswith("'") and name.endswith("'"):
        name = name[1:-1]

    if is_entity:
        # remove Chinese quotes
        name = name.replace(""", "").replace(""", "").replace("'", "").replace("'", "")
        # remove English queotes in and around chinese
        name = re.sub(r"['\"]+(?=[\u4e00-\u9fa5])", "", name)
        name = re.sub(r"(?<=[\u4e00-\u9fa5])['\"]+", "", name)

    return name


def clean_text(text: str) -> str:
    """Clean text by removing null bytes (0x00) and whitespace

    Args:
        text: Input text to clean

    Returns:
        Cleaned text
    """
    return text.strip().replace("\x00", "")


def check_storage_env_vars(storage_name: str) -> None:
    """Check if all required environment variables for storage implementation exist

    Args:
        storage_name: Storage implementation name

    Raises:
        ValueError: If required environment variables are missing
    """
    from aperag.graph.lightrag.kg import STORAGE_ENV_REQUIREMENTS

    required_vars = STORAGE_ENV_REQUIREMENTS.get(storage_name, [])
    missing_vars = [var for var in required_vars if var not in os.environ]

    if missing_vars:
        raise ValueError(
            f"Storage implementation '{storage_name}' requires the following "
            f"environment variables: {', '.join(missing_vars)}"
        )


class TokenTracker:
    """Track token usage for LLM calls."""

    def __init__(self):
        self.reset()

    def __enter__(self):
        self.reset()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(self)

    def reset(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0

    def add_usage(self, token_counts):
        """Add token usage from one LLM call.

        Args:
            token_counts: A dictionary containing prompt_tokens, completion_tokens, total_tokens
        """
        self.prompt_tokens += token_counts.get("prompt_tokens", 0)
        self.completion_tokens += token_counts.get("completion_tokens", 0)

        # If total_tokens is provided, use it directly; otherwise calculate the sum
        if "total_tokens" in token_counts:
            self.total_tokens += token_counts["total_tokens"]
        else:
            self.total_tokens += token_counts.get(
                "prompt_tokens", 0
            ) + token_counts.get("completion_tokens", 0)

        self.call_count += 1

    def get_usage(self):
        """Get current usage statistics."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "call_count": self.call_count,
        }

    def __str__(self):
        usage = self.get_usage()
        return (
            f"LLM call count: {usage['call_count']}, "
            f"Prompt tokens: {usage['prompt_tokens']}, "
            f"Completion tokens: {usage['completion_tokens']}, "
            f"Total tokens: {usage['total_tokens']}"
        )


class LightRAGLogger:
    """
    Unified logger for LightRAG processing progress.
    Replaces the legacy pipeline_status system with structured logging.
    """
    
    def __init__(self, prefix: str = "LightRAG", workspace: str = "default"):
        """
        Initialize the logger with custom prefix and workspace.
        
        Args:
            prefix: Log message prefix (default: "LightRAG")
            workspace: Workspace identifier for multi-tenant logging
        """
        self.prefix = prefix
        self.workspace = workspace
        self._current_job = None
        self._current_progress = {"current": 0, "total": 0}
    
    def _format_message(self, message: str, level: str = "INFO") -> str:
        """Format log message with prefix and workspace."""
        workspace_info = f"[{self.workspace}]" if self.workspace != "default" else ""
        job_info = f"[{self._current_job}]" if self._current_job else ""
        progress_info = ""
        if self._current_progress["total"] > 0:
            progress_info = f"[{self._current_progress['current']}/{self._current_progress['total']}]"
        
        return f"{self.prefix}{workspace_info}{job_info}{progress_info} {message}"
    
    def info(self, message: str):
        """Log info level message."""
        formatted_msg = self._format_message(message, "INFO")
        logger.info(formatted_msg)
    
    def warning(self, message: str):
        """Log warning level message."""
        formatted_msg = self._format_message(message, "WARNING")
        logger.warning(formatted_msg)
    
    def error(self, message: str):
        """Log error level message."""
        formatted_msg = self._format_message(message, "ERROR")
        logger.error(formatted_msg)
    
    def debug(self, message: str):
        """Log debug level message."""
        formatted_msg = self._format_message(message, "DEBUG")
        logger.debug(formatted_msg)
    
    def start_job(self, job_name: str, total_items: int = 0):
        """Start a new job with progress tracking."""
        self._current_job = job_name
        self._current_progress = {"current": 0, "total": total_items}
        self.info(f"Starting job: {job_name}" + (f" ({total_items} items)" if total_items > 0 else ""))
    
    def update_progress(self, current: int, message: str = ""):
        """Update current progress."""
        self._current_progress["current"] = current
        if message:
            self.info(message)
    
    def increment_progress(self, message: str = ""):
        """Increment progress by 1."""
        self._current_progress["current"] += 1
        if message:
            self.info(message)
    
    def finish_job(self, message: str = ""):
        """Finish current job."""
        final_message = message or f"Completed job: {self._current_job}"
        self.info(final_message)
        self._current_job = None
        self._current_progress = {"current": 0, "total": 0}
    
    def log_extraction_progress(self, current_chunk: int, total_chunks: int, entities_count: int, relations_count: int):
        """Log chunk extraction progress."""
        message = f"Chunk {current_chunk} of {total_chunks} extracted {entities_count} Ent + {relations_count} Rel"
        self.info(message)
    
    def log_stage_progress(self, stage: str, current_file: int, total_files: int, file_path: str):
        """Log stage progress for file processing."""
        message = f"{stage} stage {current_file}/{total_files}: {file_path}"
        self.info(message)
    
    def log_entity_merge(self, entity_name: str, total_fragments: int, new_fragments: int, is_llm_summary: bool = False):
        """Log entity merge operations."""
        prefix = "LLM merge N" if is_llm_summary else "Merge N"
        message = f"{prefix}: {entity_name} | {new_fragments}+{total_fragments-new_fragments}"
        self.info(message)
    
    def log_relation_merge(self, src_id: str, tgt_id: str, total_fragments: int, new_fragments: int, is_llm_summary: bool = False):
        """Log relation merge operations."""
        prefix = "LLM merge E" if is_llm_summary else "Merge E"
        message = f"{prefix}: {src_id} - {tgt_id} | {new_fragments}+{total_fragments-new_fragments}"
        self.info(message)


def create_lightrag_logger(prefix: str = "LightRAG", workspace: str = "default") -> LightRAGLogger:
    """Create a LightRAGLogger instance with specified prefix and workspace."""
    return LightRAGLogger(prefix=prefix, workspace=workspace)
