# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import inspect
import logging
import re
from dataclasses import dataclass
from hashlib import md5
from typing import Any, Pattern

from markdown_it import MarkdownIt
from markdown_it.token import Token

from aperag.docparser.base import AssetBinPart, CodePart, ImagePart, MarkdownPart, Part, TextPart, TitlePart
from aperag.docparser.utils import asset_bin_part_to_url

logger = logging.getLogger(__name__)

DATA_URI_PATTERN: Pattern = re.compile(r"!\[.*?\]\(\s*(data:.+?;base64,.+?)(?:\s+\"(.*?)\")?\)")  # 用以匹配 Markdown 格式的图片语法中内嵌的 Base64 编码图片


def parse_md(input_md: str, metadata: dict[str, Any]) -> list[Part]:  # 基于原始文件元数据，对markdown文件进行分段解析
    # -- 提取markdown内容中base64字符串形式的图片为资源记录，并将其替换为资源url，返回处理后的markdown文本和资源记录列表
    input_md, asset_bin_parts = extract_data_uri(input_md, metadata)
    # -- 构建markdown文件实例
    md_part = MarkdownPart(markdown=input_md, metadata=metadata)
    """
    # markdown_it.MarkdownIt 类：Markdown 处理的“核心引擎”
    `MarkdownIt` 是 `markdown_it` 库的入口类，本质是 **“Markdown 文本→结构化数据→目标格式”的转换器**，既负责按规则解析 Markdown 语法，又能将解析结果渲染为 HTML 等可展示格式，同时支持高度定制，是 Python 中处理 Markdown 的“全能工具”。
    
    ## 一、核心定位：解决“Markdown 怎么转、怎么改”的问题
    日常处理 Markdown 时，你可能需要：
    - 把 `# 标题` 转成 `<h1>标题</h1>`（基础渲染）；
    - 支持表格、数学公式等扩展语法；
    - 自定义链接样式（如加 `target="_blank"`）；
    - 先提取 Markdown 里的所有标题，再渲染。
    
    这些需求都需要 `MarkdownIt` 来协调——它一边管“解析语法”，一边管“渲染输出”，还能让你插入自定义逻辑。
    
    ## 二、核心能力：两步完成 Markdown 处理
    `MarkdownIt` 的工作流程分“解析”和“渲染”两步，你可以按需“一站式执行”或“分步控制”。
    
    ### 1. 第一步：解析（Markdown 文本 → 令牌流）
    Markdown 是“带符号的纯文本”（比如 `**加粗**`），`MarkdownIt` 会先按语法规则（如 CommonMark 标准）把文本拆成 **“令牌（tokens）”**——一种描述“这是什么元素”的结构化数据（类似“语法树的简化版”）。
    
    每个令牌包含：
    - `type`：元素类型（如 `heading_open` 是标题开始，`strong_close` 是加粗结束）；
    - `tag`：对应 HTML 标签（如 `h1`、`strong`）；
    - `content`：元素内容（如标题文本、链接地址）。
    
    **示例：解析简单 Markdown**
    ```python
    import markdown_it
    
    md = markdown_it.MarkdownIt()  # 初始化引擎
    # 解析 Markdown 文本，得到令牌流
    tokens = md.parse("## 我是二级标题，带**加粗**")
    
    # 打印令牌流（简化输出）
    for token in tokens:
        print(f"类型：{token.type:15} | 标签：{token.tag:5} | 内容：{token.content[:20]}")
    ```
    输出结果（能清晰看到元素结构）：
    ```
    类型：heading_open     | 标签：h2    | 内容：
    类型：inline           | 标签：      | 内容：我是二级标题，带
    类型：strong_open      | 标签：strong| 内容：
    类型：text             | 标签：      | 内容：加粗
    类型：strong_close     | 标签：strong| 内容：
    类型：heading_close    | 标签：h2    | 内容：
    ```
    
    ### 2. 第二步：渲染（令牌流 → 目标格式）
    解析得到的令牌流是“结构化数据”，`MarkdownIt` 会用内置的“渲染器”把它转成目标格式（默认是 HTML，也可扩展为 JSON、LaTeX 等）。
    
    **示例：渲染为 HTML**
    ```python
    # 方式1：一站式解析+渲染（最常用）
    html = md.render("## 我是二级标题，带**加粗**")
    print(html)  # 输出：<h2>我是二级标题，带<strong>加粗</strong></h2>
    
    # 方式2：分步渲染（先解析得到 tokens，再渲染）
    tokens = md.parse("## 我是二级标题，带**加粗**")
    html = md.renderer.render(tokens, md.options, {})  # 用解析器的渲染器处理令牌流
    ```
    
    ## 三、实用特性：满足多样化需求
    `MarkdownIt` 不只是“简单转 HTML”，更强大的是支持 **扩展和定制**，覆盖大多数实际场景。
    
    ### 1. 启用扩展语法（表格、脚注等）
    默认只支持 CommonMark 基础语法（标题、列表、链接等），若需要表格、删除线等扩展功能，可通过 `enable()` 开启：
    ```python
    # 初始化引擎，并启用“表格”和“删除线”语法
    md = markdown_it.MarkdownIt().enable("table").enable("strikethrough")
    
    # 渲染表格
    table_md = '''
    | 姓名 | 年龄 |
    |------|------|
    | 张三 | 25   |
    | 李四 | 30   |
    '''
    html = md.render(table_md)
    print(html)  # 输出带 <table> 标签的 HTML
    ```
    
    ### 2. 用插件扩展功能（如数学公式）
    `markdown_it` 生态有很多第三方插件，比如支持数学公式（`$E=mc^2$`）的 `markdown-it-math`，只需通过 `use()` 注册即可：
    ```bash
    # 先安装插件
    pip install markdown-it-math
    ```
    ```python
    from markdown_it.extensions.math import math_plugin
    
    # 注册数学公式插件
    md = markdown_it.MarkdownIt().use(math_plugin)
    
    # 渲染数学公式
    math_md = "质能方程：$E=mc^2$，积分公式：$$\\int_0^1 x dx$$"
    html = md.render(math_md)
    # 输出：带 <span class="math"> 标签的 HTML（需配合 MathJax 等库渲染公式）
    ```
    
    ### 3. 自定义渲染规则（改标签、加属性）
    如果默认渲染不符合需求（比如想让所有链接打开新窗口），可以重写特定令牌的渲染逻辑：
    ```python
    md = markdown_it.MarkdownIt()
    
    # 自定义“链接开始”令牌的渲染规则
    def custom_link_render(tokens, idx, options, env, renderer):
        # 获取链接地址
        link_href = tokens[idx].attrGet("href")
        # 输出带 target="_blank" 的 <a> 标签
        return f'<a href="{link_href}" target="_blank" rel="noopener">'
    
    # 注册规则：让“link_open”类型的令牌用自定义函数渲染
    md.add_render_rule("link_open", custom_link_render)
    
    # 测试渲染链接
    html = md.render("[访问示例](https://example.com)")
    print(html)  # 输出：<a href="https://example.com" target="_blank" rel="noopener">访问示例</a>
    ```
    
    ### 4. 提取结构化数据（如所有标题）
    通过解析得到的令牌流，还能提取 Markdown 中的特定信息（比如所有标题），无需渲染 HTML：
    ```python
    md = markdown_it.MarkdownIt()
    tokens = md.parse('''
    # 一级标题
    ## 二级标题1
    ### 三级标题
    ## 二级标题2
    ''')
    
    # 遍历令牌流，提取所有标题
    headings = []
    for i, token in enumerate(tokens):
        if token.type == "heading_open":  # 找到标题开始令牌
            level = int(token.tag[1])  # 从 h1/h2 中提取标题级别
            content_token = tokens[i+1]  # 标题内容在“inline”令牌中
            headings.append({"level": level, "text": content_token.content})
    
    print(headings)
    # 输出：[
    #   {"level": 1, "text": "一级标题"},
    #   {"level": 2, "text": "二级标题1"},
    #   {"level": 3, "text": "三级标题"},
    #   {"level": 2, "text": "二级标题2"}
    # ]
    ```
    
    ## 四、典型使用场景
    | 场景                | 用 MarkdownIt 做什么？                                  |
    |---------------------|---------------------------------------------------------|
    | 博客/笔记系统       | 把用户写的 Markdown 文章转成 HTML 页面展示              |
    | 文档生成工具        | 把 Markdown 接口文档转成 HTML/PDF，或提取目录结构        |
    | 编辑器实时预览      | 输入 Markdown 时，实时解析+渲染，显示预览效果            |
    | 内容审核            | 解析 Markdown 令牌流，过滤不安全标签（如 `<script>`）    |
     
    ## 总结
    `MarkdownIt` 类的核心价值是：**把“杂乱的 Markdown 文本”变成“可控的结构化数据”，再转成你需要的格式**。它既遵守标准（保证兼容性），又支持扩展（满足个性化需求），是 Python 处理 Markdown 时的“首选工具”——无论是简单的 HTML 渲染，还是复杂的语法扩展、数据提取，都能通过它实现。
    """
    md = MarkdownIt("gfm-like", options_update={"inline_definitions": True})  # MarkdownIt是将markdown文本→结构化数据→目标格式的转换器
    tokens = md.parse(input_md)  # 解析【Markdown 文本 → 令牌流】【注意后续没有继续使用markdownit将令牌流渲染为特定格式】
    converter = PartConverter()
    parts = converter.convert_all(tokens, metadata)  # 将令牌流转化为**

    return [md_part] + asset_bin_parts + parts


def extract_data_uri(text: str, metadata: dict[str, Any]) -> tuple[str, list[Part]]:  # 提取markdown内容中base64字符串形式的图片为资源记录，并将其替换为资源url
    asset_bin_parts: list[Part] = []
    for match in DATA_URI_PATTERN.finditer(text):  # 正则匹配 Markdown 格式的图片语法中内嵌的 Base64 编码图片
        data_uri = match.group(1)  # 形如“data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...”

        try:
            mime_type, encoded_data = data_uri.split("base64,")  # 形如：mime_type=data:image/png;  encoded_data=iVBORw0KGgoAAAANSUhEUgAA...
            mime_type = mime_type[5:-1]  # Remove 'data:' and the trailing ';'  获取图片类型
            binary_data = base64.b64decode(encoded_data)  # 解码base64字符串，得到二进制数据
            """
            第二行代码 `asset_id = md5(binary_data).hexdigest()` 的核心作用是：**对 Base64 解码后的二进制数据（如图片、文件等）计算其 MD5 哈希值，并将哈希值转为十六进制字符串，最终生成一个唯一的“资源标识（asset_id）”**。

            下面从“函数作用”“各环节逻辑”“实际用途”三方面详细拆解：            
            
            ### 1. 核心函数与参数解析
            先明确代码中关键函数的作用：
            - `md5(...)`：这里是 Python 中用于计算 **MD5 消息摘要（哈希值）** 的函数（通常来自 `hashlib` 库，完整写法为 `hashlib.md5()`）。MD5 是一种哈希算法，能将任意长度的输入数据（如二进制、文本）压缩为 **128 位（16 字节）的固定长度哈希值**，可理解为数据的“数字指纹”。
            - `binary_data`：输入参数，即第一行 `base64.b64decode(encoded_data)` 解码得到的 **原始二进制数据**（比如 Base64 编码的图片解码后得到的 `b'\xff\xd8\xff\xe0\x00\x10JFIF...'` 格式二进制）。
            - `.hexdigest()`：将 MD5 计算出的 **16 字节二进制哈希值** 转为 **32 位的十六进制字符串**（如 `'e8a4f32d7c91b5a83210e7b9c3d2f1a0'`），方便存储、传输和肉眼识别（二进制哈希值可读性差，十六进制是哈希值的常用展示形式）。
                        
            ### 2. 完整逻辑链：从 Base64 解码到生成 asset_id
            结合第一行代码，整体逻辑是“处理资源→生成唯一标识”的流程：
            1. 第一行：`base64.b64decode(encoded_data)`  
               将传入的 **Base64 编码字符串**（如图片的 Base64 格式）解码为 **原始二进制数据**（这是资源的“真实数据形态”，比如图片文件的二进制内容）。
            2. 第二行：`md5(binary_data).hexdigest()`  
               对“真实二进制数据”计算 MD5 哈希值→转为十六进制字符串→作为 `asset_id`。  
               关键特性：**相同的二进制数据，必然生成相同的 MD5 哈希值；不同的二进制数据，生成相同 MD5 哈希值的概率极低（可忽略，视为“唯一”）**。
                        
            ### 3. 实际用途：为什么要生成 asset_id？
            `asset_id` 本质是基于“数据内容”生成的 **唯一资源标识**，常见用途有 3 类：
            #### （1）作为资源的“唯一ID”，用于存储/索引
            比如处理 Base64 编码的图片时，生成 `asset_id` 作为图片的“文件名”或“数据库主键”：
            - 示例：一张图片解码后的二进制数据计算出的 MD5 哈希值为 `e8a4f32d...`，则可将图片保存为 `e8a4f32d...png`，或在数据库中用这个 `asset_id` 标识该图片，避免重复存储（相同图片会生成相同 `asset_id`，直接复用即可）。
            
            #### （2）校验数据完整性（防篡改/防损坏）
            MD5 哈希值是数据的“数字指纹”，可用于验证数据是否被修改或传输损坏：
            - 比如接收 Base64 编码的文件时，先解码得到 `binary_data`，计算 `asset_id`，再与发送方提供的“原始 MD5 哈希值”对比——若一致，说明数据完整未篡改；若不一致，说明数据损坏或被修改。
            
            #### （3）去重：避免重复处理相同资源
            若多次接收相同的 Base64 编码数据（比如重复上传同一张图片），通过 `asset_id` 可快速判断是否为“已处理过的资源”：
            - 示例：数据库中已存储 `asset_id = e8a4f32d...` 的图片，当再次收到相同 Base64 编码时，计算出相同 `asset_id`，直接跳过处理流程，减少重复计算和存储开销。
            
            ### 4. 注意事项（潜在风险）
            - **MD5 的安全性局限**：MD5 算法存在“哈希碰撞”风险（理论上不同数据可能生成相同哈希值），且不具备抗篡改的密码学安全性——若 `asset_id` 用于“敏感场景”（如用户身份验证、数据加密），需改用更安全的算法（如 SHA-256，对应 `hashlib.sha256()`）；但用于“资源标识、完整性校验、去重”等非敏感场景，MD5 足够高效且满足需求。
            - **依赖 `hashlib` 库**：代码中 `md5()` 需提前导入 `hashlib` 库，完整写法应为：
              ```python
              import base64
              import hashlib
            
              encoded_data = "Base64编码字符串"
              binary_data = base64.b64decode(encoded_data)
              asset_id = hashlib.md5(binary_data).hexdigest()  # 完整写法
              ```
            
            ### 总结
            第二行代码的核心是 **“基于资源的二进制内容生成唯一标识”**：通过 MD5 哈希算法将解码后的二进制数据转为 32 位十六进制字符串，既保证了“相同资源同一标识”，又便于后续的存储、索引、完整性校验和去重，是处理文件、图片等二进制资源时的常用设计。
            """
            asset_id = md5(binary_data).hexdigest()  # 利用哈希映射根据资源内容【二进制形式】生成资源唯一标识
            asset_bin_part = AssetBinPart(
                asset_id=asset_id,
                data=binary_data,
                mime_type=mime_type,
                metadata=metadata,
            )  # 构建资源记录
            asset_bin_parts.append(asset_bin_part)  # 将资源记录收集到资源列表中

            asset_url = asset_bin_part_to_url(asset_bin_part)  # 从资源记录构造资源url，形如：f"asset://{part.asset_id}?mime_type={quote_plus(part.mime_type)}"
            text = text.replace(data_uri, asset_url)  # 将markdown文本中的base64图片替换为资源url
        except Exception as e:
            logger.warning(f"Error processing data URI: {e}")

    return text, asset_bin_parts  # 返回处理后【将markdown文本中的base64图片替换为资源url】的markdown文本和该markdown对应的资源列表


class PartConverter:
    @dataclass
    class Context:
        nesting: int = 0
        ordinal: int = 1
        pause_extraction: bool = False

    class Nester:
        def __init__(self, ctx: "PartConverter.Context"):
            self.ctx = ctx

        def __enter__(self):
            self.ctx.nesting += 1
            return self.ctx

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.ctx.nesting -= 1
            return False

    class OrderedListNester:
        def __init__(self, ctx: "PartConverter.Context"):
            self.ctx = ctx
            self.old_ordinal = self.ctx.ordinal

        def __enter__(self):
            self.ctx.ordinal = 1
            self.ctx.nesting += 1
            return self.ctx

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.ctx.ordinal = self.old_ordinal
            self.ctx.nesting -= 1
            return False

    class PauseExtraction:
        def __init__(self, ctx: "PartConverter.Context"):
            self.ctx = ctx
            self.old_val = ctx.pause_extraction

        def __enter__(self):
            self.ctx.pause_extraction = True
            return self.ctx

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.ctx.pause_extraction = self.old_val
            return False

    def __init__(self):
        prefix = "_convert_"
        """
        支持下述token.type
        blockquote_open
        code_block
        fence
        heading_open
        inline
        hr
        html_block
        paragraph_open
        ordered_list_open
        bullet_list_open
        list_item_open
        definition
        table_open
        thead_open
        tbody_open
        tr_open
        th_open
        td_open
        """
        self.handlers = {
            k[len(prefix) :]: v
            for k, v in inspect.getmembers(self, predicate=inspect.ismethod)  # predicate参数表示当前对象的成员需要是方法
            if k.startswith(prefix) and len(k) > len(prefix)  # 方法名称限制条件：以_convert_开头，且方法名称含有其他字符
        }  # 返回对象的所有方法按名称排序的（name, value）对。

    def convert(self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]) -> tuple[list[Part], int]:
        if idx >= len(tokens):
            return [], idx
        token = tokens[idx]
        """
        支持下述token.type
        blockquote_open
        code_block
        fence
        heading_open
        inline
        hr
        html_block
        paragraph_open
        ordered_list_open
        bullet_list_open
        list_item_open
        definition
        table_open
        thead_open
        tbody_open
        tr_open
        th_open
        td_open
        """
        handler = self.handlers.get(token.type)
        if handler:  # TODO 至此~
            return handler(ctx, tokens, idx, metadata.copy())
        logger.warning(f"Unhandled token type: {token}")
        if token.content:
            meta = metadata.copy()
            if token.map:
                meta["md_source_map"] = token.map
            return [TextPart(content=token.content, metadata=meta)], idx + 1
        return [], idx + 1

    def convert_all(self, tokens: list[Token], metadata: dict[str, Any]) -> list[Part]:
        """
        参数说明：
            tokens：令牌流，有markdownit工具解析markdown文本得到，每个token是一个实例，包含三个属性【type类型\tag标签\content内容】
                例如：markdown文本为“## 我是二级标题，带**加粗**”
                执行下述操作：
                >>> import markdown_it
                >>> md = markdown_it.MarkdownIt("gfm-like", options_update={"inline_definitions": True})
                >>> tokens = md.parse('## 我是二级标题，带**加粗**')
                >>> for token in tokens:
                ...         print(f"类型：{token.type:15} | 标签：{token.tag:5} | 内容：{token.content[:20]}")
                使用markdownit解析后的令牌流，打印结果为：
                类型：heading_open    | 标签：h2    | 内容：
                类型：inline          | 标签：      | 内容：我是二级标题，带**加粗**
                类型：heading_close   | 标签：h2    | 内容：
                打印结果解释：
                    类型：heading_open表示标题起始标签，inline表示当前内容为标签内文本，heading_close表示标题结束标签
                    标签：HTML标签
                    内容：文本内容，标签对应的内容为空
            metadata：原始文件元数据
        """
        if metadata is None:
            metadata = {}
        result: list[Part] = []  # 初始化文件列表
        ctx = self.Context()
        # -- 从0索引位置，动态处理令牌流，直到令牌流处理完毕
        pos = 0
        while pos < len(tokens):
            parts, pos = self.convert(ctx, tokens, pos, metadata)  # 从tokens的位置pos处开始处理令牌流，得到文件实例列表和下一次要处理的起始位置pos
            result.extend(parts)  # 收集当前生成的文件实例列表
        return result

    def convert_until_close(
        self, ctx: Context, close_ttype: str, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        result: list[Part] = []
        pos = idx
        while pos < len(tokens):
            next_token = tokens[pos]
            if next_token.type == close_ttype:
                pos = pos + 1
                break
            parts, pos = self.convert(ctx, tokens, pos, metadata)
            result.extend(parts)
        return result, pos

    def _extract_image_parts(self, ctx: Context, tokens: list[Token], metadata: dict[str, Any]) -> list[Part]:
        if ctx.pause_extraction:
            return []
        result: list[Part] = []
        for token in tokens:
            if not token.children:
                continue
            for child in token.children:
                if child.children:
                    result.extend(self._extract_image_parts(ctx, child.children, metadata))
                if child.type != "image":
                    continue
                if child.meta.get("_extracted_image_token", False):
                    continue
                child.meta["_extracted_image_token"] = True
                meta = metadata.copy()
                meta["md_source_map"] = child.map
                if child.type == "image":
                    img_part = ImagePart(
                        metadata=meta,
                        url=child.attrs.get("src", ""),
                        alt_text=child.content,
                        title=child.attrs.get("title", None),
                    )
                    result.append(img_part)
        return result

    # ======================================================
    # handlers
    # ======================================================

    def _convert_blockquote_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        with self.Nester(ctx):
            parts, pos = self.convert_until_close(ctx, "blockquote_close", tokens, idx + 1, metadata)

        token = tokens[idx]
        for part in parts:
            if not isinstance(
                part,
                (
                    TextPart,
                    TitlePart,
                ),
            ):
                continue
            if part.content is not None:
                lines = part.content.split("\n")
                # Add "> " prefix to each line
                part.content = "\n".join([token.markup + " " + line for line in lines])

        return parts, pos

    @staticmethod
    def _to_code_content(code: str, lang: str | None = None) -> str:
        backticks = "```"
        for i in range(10):
            if backticks not in code:
                break
            backticks += "`"
        code = code.strip()
        if lang:
            return f"{backticks}{lang}\n{code}\n{backticks}"
        return f"{backticks}\n{code}\n{backticks}"

    def _convert_code_block(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        token = tokens[idx]
        metadata["md_source_map"] = token.map
        metadata["md_nesting"] = ctx.nesting
        code = self._to_code_content(token.content, None)
        return [CodePart(content=code, metadata=metadata)], idx + 1

    def _convert_fence(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        token = tokens[idx]
        metadata["md_source_map"] = token.map
        metadata["md_nesting"] = ctx.nesting
        lang = None
        if token.info:
            lang = token.info
            metadata["code_lang"] = lang
        code = self._to_code_content(token.content, lang)
        return [CodePart(content=code, metadata=metadata, lang=lang)], idx + 1

    def _convert_heading_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        parts, pos = self.convert_until_close(ctx, "heading_close", tokens, idx + 1, metadata)
        text = ""
        for part in parts:
            if part.content is not None:
                text += part.content
        token = tokens[idx]
        metadata["md_source_map"] = token.map
        metadata["md_nesting"] = ctx.nesting
        if token.markup in ["=", "-"]:
            # It's a lheading
            if token.markup == "=":
                level = 1
            else:
                level = 2
        else:
            level = len(token.markup)  # Count how many "#"
        title = ("#" * level) + " " + text
        return [TitlePart(content=title, metadata=metadata, level=level)], pos

    def _convert_inline(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        token = tokens[idx]
        img_parts = self._extract_image_parts(ctx, tokens[idx : idx + 1], metadata)
        metadata["md_source_map"] = token.map
        metadata["md_nesting"] = ctx.nesting
        return [TextPart(content=token.content, metadata=metadata)] + img_parts, idx + 1

    def _convert_hr(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        token = tokens[idx]
        metadata["md_source_map"] = token.map
        metadata["md_nesting"] = ctx.nesting
        return [TextPart(content=token.markup, metadata=metadata)], idx + 1

    def _convert_html_block(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        token = tokens[idx]
        metadata["md_source_map"] = token.map
        metadata["md_nesting"] = ctx.nesting
        return [TextPart(content=token.content, metadata=metadata)], idx + 1

    def _convert_paragraph_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        parts, pos = self.convert_until_close(ctx, "paragraph_close", tokens, idx + 1, metadata)
        return parts, pos

    def _convert_ordered_list_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        with self.OrderedListNester(ctx):
            parts, pos = self.convert_until_close(ctx, "ordered_list_close", tokens, idx + 1, metadata)
            return parts, pos

    def _convert_bullet_list_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        with self.Nester(ctx):
            parts, pos = self.convert_until_close(ctx, "bullet_list_close", tokens, idx + 1, metadata)
            return parts, pos

    def _convert_list_item_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        parts, pos = self.convert_until_close(ctx, "list_item_close", tokens, idx + 1, metadata)
        token = tokens[idx]
        if len(token.info) != 0:
            # Item of ordered list
            item_marker = str(ctx.ordinal) + token.markup + " "
            ctx.ordinal += 1
        else:
            # Item of unordered list
            item_marker = token.markup + " "
        if len(parts) == 0:
            # Empty item, e.g. "2. "
            metadata["md_source_map"] = token.map
            metadata["md_nesting"] = ctx.nesting
            return [TextPart(content=item_marker, metadata=metadata)], pos

        result = []
        first_part = parts[0]
        if isinstance(first_part, TextPart):
            # If the first block is a paragraph-like block, then prepend the marker:
            #   item content,     =>  1. item content,
            #   the second line          the second line
            lines = (first_part.content or "").split("\n")
            if len(lines) > 0:
                spaces = " " * len(item_marker)
                lines[0] = item_marker + lines[0]
                for i in range(1, len(lines)):
                    lines[i] = spaces + lines[i]
            else:
                lines.append(item_marker)

            first_part.content = "\n".join(lines)
            result.append(first_part)
        else:
            # If the first block is a code block, or something else,
            # we don't modify the content of the block.
            meta = metadata.copy()
            meta["md_source_map"] = token.map
            meta["md_nesting"] = ctx.nesting
            result.append(TextPart(content=item_marker, metadata=meta))
            result.append(first_part)

        spaces = "    "
        for part in parts[1:]:
            # Adjust indention for paragraph blocks
            if isinstance(part, TextPart):
                lines = (part.content or "").split("\n")
                lines = [spaces + line for line in lines]
                if len(lines) > 0:
                    part.content = "\n".join(lines)

            result.append(part)

        return result, pos

    def _convert_definition(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        token = tokens[idx]
        tm = token.meta or {}
        content = f"[{tm.get('label')}]: {tm.get('url')}"
        title = tm.get("title")
        if title:
            content = content + f" ({title})"
        metadata["md_source_map"] = token.map
        metadata["md_nesting"] = ctx.nesting
        return [TextPart(content=content, metadata=metadata)], idx + 1

    def _convert_table_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        # Image parts can interfere with table processing. For example, a tr might
        # mistakenly identify an ImagePart as a separate column, leading to errors.
        # Therefore, we temporarily disable image extraction and handle it after
        # the entire table has been processed.
        with self.Nester(ctx):
            with self.PauseExtraction(ctx):
                parts, pos = self.convert_until_close(ctx, "table_close", tokens, idx + 1, metadata)
        img_parts = self._extract_image_parts(ctx, tokens[idx:pos], metadata)
        # Parts should contain two items, thead and tbody
        text = "\n".join([part.content for part in parts if part.content is not None])
        metadata["md_source_map"] = tokens[idx].map
        metadata["md_nesting"] = ctx.nesting
        return [TextPart(content=text, metadata=metadata)] + img_parts, pos

    def _convert_thead_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        parts, pos = self.convert_until_close(ctx, "thead_close", tokens, idx + 1, metadata)
        if len(parts) == 0:
            return [], pos
        # Parts should contain one item, which is a tr
        column_count = parts[0].metadata.get("column_count", 0)
        if column_count == 0:
            return [], pos
        text = parts[0].content or ""
        text += "\n" + ("|---" * column_count) + "|"
        return [TextPart(content=text, metadata=metadata)], pos

    def _convert_tbody_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        parts, pos = self.convert_until_close(ctx, "tbody_close", tokens, idx + 1, metadata)
        text = "\n".join([part.content for part in parts if part.content is not None])
        return [TextPart(content=text, metadata=metadata)], pos

    @staticmethod
    def _escape_cell(text: str) -> str:
        text = text.replace("|", "\\|")
        text = text.replace("\r", "")
        text = text.replace("\n", "<br>")
        return text

    def _convert_tr_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        parts, pos = self.convert_until_close(ctx, "tr_close", tokens, idx + 1, metadata)
        if len(parts) == 0:
            return [], pos
        text = ""
        for part in parts:
            text += "| "
            if part.content is not None:
                text += self._escape_cell(part.content) + " "
        text += "|"
        metadata["column_count"] = len(parts)
        return [TextPart(content=text, metadata=metadata)], pos

    def _convert_th_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        parts, pos = self.convert_until_close(ctx, "th_close", tokens, idx + 1, metadata)
        text = ""
        for part in parts:
            if part.content is not None:
                text += part.content
        return [TextPart(content=text, metadata=metadata)], pos

    def _convert_td_open(
        self, ctx: Context, tokens: list[Token], idx: int, metadata: dict[str, Any]
    ) -> tuple[list[Part], int]:
        parts, pos = self.convert_until_close(ctx, "td_close", tokens, idx + 1, metadata)
        text = ""
        for part in parts:
            if part.content is not None:
                text += part.content
        return [TextPart(content=text, metadata=metadata)], pos
