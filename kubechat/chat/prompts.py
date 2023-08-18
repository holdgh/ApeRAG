ENGLISH_PROMPT_TEMPLATE = (
    "### Human:\n"
    "The original question is as follows: {query_str}\n"
    "We have provided an existing answer: {existing_answer}\n"
    "We have the opportunity to refine the existing answer "
    "(only if needed) with some more context below.\n"
    "Given the new context, refine and synthesize the original answer to better \n"
    "answer the question. Please think it step by step and make sure that the refine answer is less than 50 words. \n"
    "### Assistant :\n"
)

CHINESE_PROMPT_TEMPLATE = (
    "### 人类：\n"
    "原问题如下：{query_str}\n"
    "我们已经有了一个答案：{existing_answer}\n"
    "我们有机会完善现有的答案（仅在需要时），下面有更多上下文。\n"
    "根据新提供的上下文信息，优化现有的答案，以便更好的回答问题\n"
    "请一步一步思考，并确保优化后的答案少于 50个字。\n"
    "### 助理："
)

DEFAULT_ENGLISH_PROMPT_TEMPLATE_V2 = """
Context information is below. \n
---------------------\n
{context}
\n---------------------\n
Given the context information, please think step by step and answer the question: {query}\n

Please make sure that the answer is accurate and concise.

If you don't know the answer, just say that you don't know, don't try to make up an answer.
"""

DEFAULT_CHINESE_PROMPT_TEMPLATE_V2 = """
上下文信息如下:\n
----------------\n
{context}
\n--------------------\n

根据提供的markdown格式的上下文信息，请一步一步思考，然后回答问题：{query}。

请确保回答准确和简洁，如果你不知道答案，就直接说你不知道，不要试图编造一个答案 。

"""

DEFAULT_MODEL_PROMPT_TEMPLATES = {
    "vicuna-13b": DEFAULT_ENGLISH_PROMPT_TEMPLATE_V2,
    "baichuan-13b": DEFAULT_CHINESE_PROMPT_TEMPLATE_V2,
}

