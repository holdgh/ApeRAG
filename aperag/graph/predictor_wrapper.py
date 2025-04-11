# from typing import Optional, List, Dict
# from aperag.llm.base import Predictor
#
#
# async def llm_model_func_async(
#     predictor: Predictor,
#     prompt: str,
#     system_prompt: Optional[str] = None,
#     history_messages: Optional[List[Dict[str, str]]] = None,
#     **kwargs  # Catch other potential args like keyword_extraction, temperature etc.
# ) -> str:
#     """
#     Asynchronous wrapper for Predictor.agenerate_stream to match LightRAG's
#     llm_model_func signature, returning a complete string.
#
#     Args:
#         predictor: An instance of your Predictor class.
#         prompt: The user's current prompt.
#         system_prompt: Optional system message.
#         history_messages: Optional list of previous messages [{'role': ..., 'content': ...}].
#         **kwargs: Additional keyword arguments (currently ignored by this wrapper,
#                   but captured to match the signature). Could be used to override
#                   predictor settings if the predictor's methods supported it.
#
#     Returns:
#         The complete generated response string from the LLM.
#     """
#     predictor_history: List[Dict[str, str]] = []
#     use_memory = False
#
#     if system_prompt:
#         predictor_history.append({"role": "system", "content": system_prompt})
#         use_memory = True # If system prompt exists, we need to use history
#
#     if history_messages:
#         # Ensure history_messages is a list, even if None was passed
#         predictor_history.extend(history_messages)
#         use_memory = True # If history exists, use it
#
#     # Check if predictor itself needs temperature or max_tokens override from kwargs
#     # Note: The current Predictor sets these in __init__. This wrapper doesn't
#     # dynamically change them per-call unless predictor.agenerate_stream supports it.
#     # We pass predictor_history directly. The 'memory' flag controls if predictor
#     # prepends this history internally based on its logic.
#     # print(f"DEBUG: Calling agenerate_stream with history={predictor_history}, prompt='{prompt}', memory={use_memory}")
#
#     full_response = ""
#     try:
#         async for token in predictor.agenerate_stream(
#             history=predictor_history, # Pass the constructed history
#             prompt=prompt,
#             memory=use_memory # Signal to the predictor whether to use the history
#         ):
#             if token: # Ensure token is not None or empty before appending
#                 full_response += token
#     except Exception as e:
#         print(f"Error collecting stream from agenerate_stream: {e}")
#         # Depending on desired behavior, return partial response or an error string
#         return f"[ERROR in llm_model_func_async: {e}]"
#         # Or re-raise the exception: raise e
#
#     return full_response
#
#
# def llm_model_func_sync(
#     predictor: Predictor,
#     prompt: str,
#     system_prompt: Optional[str] = None,
#     history_messages: Optional[List[Dict[str, str]]] = None,
#     **kwargs
# ) -> str:
#     """
#     Synchronous wrapper for Predictor.generate_stream to match LightRAG's
#     llm_model_func signature (if needed for sync contexts), returning a complete string.
#
#     Args:
#         predictor: An instance of your Predictor class.
#         prompt: The user's current prompt.
#         system_prompt: Optional system message.
#         history_messages: Optional list of previous messages [{'role': ..., 'content': ...}].
#         **kwargs: Additional keyword arguments.
#
#     Returns:
#         The complete generated response string from the LLM.
#     """
#     predictor_history: List[Dict[str, str]] = []
#     use_memory = False
#
#     if system_prompt:
#         predictor_history.append({"role": "system", "content": system_prompt})
#         use_memory = True
#
#     if history_messages:
#         predictor_history.extend(history_messages)
#         use_memory = True
#
#     # print(f"DEBUG: Calling generate_stream with history={predictor_history}, prompt='{prompt}', memory={use_memory}")
#
#     full_response = ""
#     try:
#         for token in predictor.generate_stream(
#             history=predictor_history,
#             prompt=prompt,
#             memory=use_memory
#         ):
#             if token:
#                 full_response += token
#     except Exception as e:
#         print(f"Error collecting stream from generate_stream: {e}")
#         return f"[ERROR in llm_model_func_sync: {e}]"
#         # Or re-raise the exception: raise e
#
#     return full_response
