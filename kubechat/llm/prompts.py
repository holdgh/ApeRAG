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

Don't repeat yourself.
"""

DEFAULT_CHINESE_PROMPT_TEMPLATE_V2 = """
候选答案信息如下
----------------
{context}
--------------------

你是一个根据提供的候选答案信息组织回答的专家，你的回答严格限定于给你提供的信息，如果候选答案少于50个字，就原样输出。
 
你需要谨慎准确的根据提供的markdown格式的信息，然后回答问题：{query}。
 
请一步一步思考，请确保回答准确和简洁，如果你不知道答案，就直接说你不知道，不要试图编造一个答案。

问题只回答一次。
"""

DEFAULT_ENGLISH_PROMPT_TEMPLATE_V3 = """
You are an expert at answering questions based on dialogue history and provided candidate answer. 

Given the dialogue history and the candidate answer, you need to answer the question: {query}。

Please think step by step, please make sure that the answer is accurate and concise.

If the answer cannot be found in the dialogue history and candidate answer, \
simply state that you do not know. Do not attempt to fabricate an answer.

Don't repeat yourself.

Candidate answer is below:
----------------
{context}
--------------------
"""

DEFAULT_CHINESE_PROMPT_TEMPLATE_V3 = """
你是一个根据对话记录和候选答案来回答问题的专家，你的回答严格限定于刚才的对话记录和下面给你提供的候选答案。

你需要基于刚才的对话记录，谨慎准确的依据markdown格式的候选答案，来回答问题：{query}。

请一步一步思考，请确保回答准确和简洁，如果从对话记录和候选答案中找不出回答，就直接说你不知道，不要试图编造一个回答。

问题只回答一次。

候选答案如下:
----------------
{context}
--------------------
"""

DEFAULT_MODEL_PROMPT_TEMPLATES = {
    "vicuna-13b": DEFAULT_ENGLISH_PROMPT_TEMPLATE_V2,
    "baichuan-13b": DEFAULT_CHINESE_PROMPT_TEMPLATE_V2,
}

DEFAULT_MODEL_MEMOTY_PROMPT_TEMPLATES = {
    "vicuna-13b": DEFAULT_ENGLISH_PROMPT_TEMPLATE_V3,
    "baichuan-13b": DEFAULT_CHINESE_PROMPT_TEMPLATE_V3,
}


QUESTION_EXTRACTION_PROMPT_TEMPLATE = """

上下文信息如下:\n
-----------------------------\n
{context}
\n-----------------------------\n

你是一个从文档中提取信息以便对人们进行问答的专家。根据提供的上下文信息，你需要编写一个有编号的问题列表，这些问题可以仅仅根据给定的上下文信息回答。
"""


QUESTION_ANSWERING_PROMPT_TEMPLATE = """
上下文信息如下：\n
-----------------------------\n
{context}
\n-----------------------------\n

你是一个专家用户，负责回答问题。根据所给的上下文信息，对问题进行全面和详尽的回答，请注意仅仅依靠给定的文本。 

"""


CHINESE_QA_EXTRACTION_PROMPT_TEMPLATE = """

文档内容如下:
-----------------------------
{context}
-----------------------------

你是一个从markdown文档中提取问题的专家，忘记你已有的知识，仅仅根据当前提供的文档信息，编写一个最有可能的问题和答案列表。

再次提醒，问题和答案必须来自于提供的文档，文档里有什么就回答什么，不要编造答案。

至少提出3个问题和答案。

"""

KEYWORD_PROMPT_TEMPLATE = """

你是从句子中找出关键词的专家，请找出下面这段话的关键词，回答要简洁，只输出找到的关键词：
--------------------
{query}
--------------------

以下是一些示例:
句子：release v1.0.2有哪些功能
关键词：v1.0.2，功能

句子：1.0.2版本有哪些功能
关键词：1.0.2，版本，功能
"""

RELATED_QUESTIONS_TEMPLATE = """
你是一个根据上下文文本来提取问题的专家。根据上下文信息和用户的问题，从深度和广度两个方面，给出3个用户可能会进一步提出的扩展问题。
回答要简洁，侧重方法而不是原理。问题不超过30字，只包含一个问号；每个问题之间用换行符分隔，没有其他无关信息。

以下是示例：
用户的问题是：怎么安装mysql
扩展问题是：
1. 安装完成后应该怎么使用MySQL？
2. 创建 MySQL 集群时，kbcli 可以提供哪些高级设置和定制选项？
3. 如何更新或扩展现有的 MySQL 集群？
------------
上下文文本如下：
---------------
{context}
---------------
用户的的问题如下：
---------------
{query}
---------------
扩展问题是：

"""

SENSITIVE_INFORMATION_TEMPLATE = """
你是一个进行敏感数据标注的人员，现在有一段文本，请指出这段文本包含的敏感信息，并且以列表的形式输出敏感信息和其在文本中的位置。如果没有敏感信息，仅输出空列表[]。
列表的每一个元素是一个json格式的信息，包括三个字段："text"字段表示文本内的敏感信息，"type"字段表示敏感信息类别，与给出的敏感信息类别一一对应，"span"表示敏感信息在文本中的位置。
注意敏感信息仅包括以下类别，不需要给出超出范围的敏感信息
敏感信息类别：{types}
以下是一些示例：
-----------------------------------
文本：
我叫张三，我毕业于哈尔滨佛学院，之后留学美国，于西太平洋大学获得汉语言文学博士学位。我的身份证号是123456789789777777。毕业后10年来先后服务于几家顶级互联网企业，包括谷歌、腾讯、阿里巴巴、百度、亚马逊等……我的密码是123478主要负责非虚拟办公场景运营和管理工作……嗯，主要是保洁工作。猎头挖我的时候，我听了他介绍贵司的岗位工作内容，很感兴趣，希望能来尝试一下。
输出：
[
{{"text": "100502199808250567", "type": "身份证号", "span": [49,67]}},
{{"text": "123478","type": "密码", "span": [117,123]}}
]

文本：
我叫张三，我毕业于哈尔滨佛学院
输出：
[]
-------------------------------------
你需要进行判断的文本如下：
-----------------------------------
{context}
-----------------------------------
"""

CLASSIFY_SENSITIVE_INFORMATION_TEMPLATE = """
你是一个进行敏感数据分析的人员，现在有一段文本，请指出这段文本是否包含敏感信息。如果包含敏感信息，回答是，如果不包含敏感信息，回答否。

注意敏感信息仅包括以下类别，不需要判断超出范围的敏感信息
敏感信息类别：{types}
以下是一些示例：
-----------------------------------
文本：
我叫张三，我毕业于哈尔滨佛学院，之后留学美国，于西太平洋大学获得汉语言文学博士学位。我的密码是123456。毕业后10年来先后服务于几家顶级互联网企业，包括谷歌、腾讯、阿里巴巴、百度、亚马逊等……我的密码是123478主要负责非虚拟办公场景运营和管理工作……嗯，主要是保洁工作。猎头挖我的时候，我听了他介绍贵司的岗位工作内容，很感兴趣，希望能来尝试一下。
输出：是

文本：
我叫张三，我毕业于哈尔滨佛学院
输出：否
-------------------------------------
你需要进行判断的文本如下：
-----------------------------------
{context}
-----------------------------------
"""

CHINESE_TRANSLATION_TEMPLATE = """
你是一个资深翻译专家，你需要理解给定的翻译要求，翻译相应的内容并给出回答
注意翻译时既要保留句子的原意，又要保证语句通畅

翻译要求如下：
-----------------------------------
{query}
-------------------------------------
"""

ENGLISH_TRANSLATION_TEMPLATE = """
You are a seasoned translation expert.
You need to understand the provided translation requirements, translate the corresponding content, and provide a response.
Ensure that the translation retains the original meaning of the sentences while maintaining fluency.

Translation requirements are below：
------------------------------------
{query}
------------------------------------
"""

CHINESE_TRANSLATION_MEMORY_TEMPLATE = """
你是一个根据对话记录和翻译要求来回答的资深翻译专家，
你需要理解给定的翻译要求，并严格根据对话记录和翻译要求，翻译相应的内容，并给出回答
注意翻译时既要保留句子的原意，又要保证语句通畅

翻译要求如下：
-----------------------------------
{query}
-------------------------------------
"""

ENGLISH_TRANSLATION_MEMORY_TEMPLATE = """
You are a seasoned translation expert who responds based on the conversation history and translation requests.
You need to understand the provided translation requirements, and strictly follow the conversation history and translation requirements to translate the corresponding content.
Ensure that the translation retains the original meaning of the sentences while maintaining fluency.

Translation requirements are below：
------------------------------------
{query}
------------------------------------
"""

CHINESE_TRANSLATION_FILE_TEMPLATE = """
你是一个资深翻译专家，现在给定翻译要求和一段需要翻译的文本
你需要理解给定的翻译要求，并严格根据翻译要求和需要翻译的文本，翻译相应的内容，并给出回答
注意翻译时既要保留句子的原意，又要保证语句通畅

翻译要求如下：
-----------------------------------
{query}
-------------------------------------
需要翻译的文本如下：
-----------------------------------
{context}
-----------------------------------
"""

ENGLISH_TRANSLATION_FILE_TEMPLATE = """
You are a seasoned translation expert, provided with translation requirements and a piece of text to be translated.
You need to understand the provided translation requirements,
and accurately translate the corresponding content based on the translation requirements and the text to be translated, then provide a response.
Ensure that the translation retains the original meaning of the sentences while maintaining fluency.

Translation requirements are below：
------------------------------------
{query}
------------------------------------
Text need to be translated is below:
--------------------------------------
{context}
--------------------------------------
"""
