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
import logging
import tempfile
import time
from pathlib import Path
from typing import Any

import requests

from aperag.aperag_config import settings
from aperag.docparser.base import (
    BaseParser,
    FallbackError,
    Part,
    PdfPart,
)
from aperag.docparser.mineru_common import middle_json_to_parts, to_md_part

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = [
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
]


class DocRayParser(BaseParser):  # pdf、word、ppt文档解析器
    name = "docray"
    """
    在RAG（检索增强生成）系统中，**DOCRAY** 是一款聚焦于**复杂文档结构化解析**的工具，其核心价值在于解决传统文档解析（如纯文本提取、简单格式拆分）中“信息碎片化、结构丢失、关键信息难定位”的问题，尤其适配RAG系统对“精准检索、上下文结构化输入”的需求。其特点可从**解析能力、适配场景、RAG协同性、功能扩展性**四个维度展开：
    
    
    ### 一、核心特点：强结构化解析，还原文档“语义+格式”双重逻辑
    DOCRAY的核心优势是突破“纯文本提取”的局限，能深度理解文档的**层级结构、语义关联和格式逻辑**，将非结构化/半结构化文档（如PDF、Word、Excel、PPT）转化为RAG系统可高效利用的“结构化信息单元”，具体表现为：
    
    #### 1. 多格式文档适配，覆盖复杂场景
    支持RAG系统中常见的各类业务文档格式，且对“高复杂度格式”的解析能力突出，避免因格式兼容性问题导致的信息丢失：
    - 基础格式：TXT、Markdown、Word（.docx）、Excel（.xlsx）、PPT（.pptx）；
    - 核心场景格式：扫描件PDF（需搭配OCR模块，支持文字提取+格式还原）、加密PDF（支持合规解密后解析）、带公式/表格/图片标注的技术文档（如产品手册、行业报告）；
    - 特殊格式：Excel中的多sheet数据关联解析、PPT中的“文本+图表+备注”联动提取（如将PPT某页的“标题+图表数据+演讲备注”整合为一个语义单元）。
    
    #### 2. 结构化提取：按“语义层级”拆分信息单元
    传统解析工具常将文档拆分为“段落”或“句子”，导致RAG检索时难以定位“完整语义块”；DOCRAY则按文档的**天然语义层级**拆分，生成更适配RAG检索的“信息单元”，例如：
    - 对“产品手册”：自动拆分为“章节（如1. 产品概述）→ 子章节（1.1 核心功能）→ 语义块（功能A的描述+参数+适用场景）”；
    - 对“合同文档”：拆分为“条款模块（如3. 付款方式）→ 子条款（3.1 付款周期）→ 关键信息点（付款周期：30天/账期、付款方式：银行转账）”；
    - 对“Excel数据表”：不仅提取单元格内容，还会保留“表头-数据行”的关联关系（如“客户ID-客户名称-订单金额”的映射），避免数据脱离上下文。
    
    #### 3. 关键信息自动标注，降低RAG检索成本
    解析过程中会自动识别并标注文档中的**核心实体、属性、关联关系**，无需依赖额外的NLP工具二次处理，直接为RAG的“精准检索”和“上下文注入”提供支持：
    - 实体标注：自动识别“产品名、日期、金额、规格、部门”等实体（如在合同中标注“甲方：XX公司”“有效期：2024-2025”）；
    - 属性关联：标注实体的属性信息（如“产品A-属性：重量5kg、价格1000元、适用场景：工业场景”）；
    - 格式标注：保留“表格、公式、图片说明”等特殊格式的标记（如在解析结果中注明“[表格1：产品A与竞品参数对比]”），方便RAG检索时优先匹配含特定格式的信息（如用户问“产品A的参数对比表”，可直接定位到标注的表格单元）。
    
    
    ### 二、RAG系统协同性：精准匹配“检索-生成”全流程需求
    DOCRAY并非独立的解析工具，其设计逻辑深度贴合RAG系统“检索准确、上下文完整、生成可靠”的核心目标，具体协同优势如下：
    
    #### 1. 提升RAG检索精度：缩小“有效上下文”范围
    RAG的检索效率依赖“检索单元与用户问题的语义匹配度”：
    - 传统解析的“大段落”中可能包含无关信息（如某段落同时讲“产品功能”和“售后政策”），导致检索时“噪音干扰”；
    - DOCRAY拆分的“语义块”（如仅包含“产品A功能描述”的单元）更聚焦单一主题，RAG向量检索时能更精准匹配用户问题（如用户问“产品A的功能”，可直接命中对应语义块，无需过滤无关内容）。
    
    #### 2. 支持跨分段/跨文档关联：为“知识串联”打基础
    针对RAG中“跨分段/跨文档检索”的场景，DOCRAY的解析结果可提供“关联线索”：
    - 跨分段关联：解析时保留“语义块的层级路径”（如“产品手册→1.1 核心功能→功能A”），当用户问题涉及多个分段（如“产品A的功能和参数”），RAG可通过层级路径快速定位同属“产品A”的功能块和参数块；
    - 跨文档关联：若多个文档涉及同一实体（如“产品A”），DOCRAY会统一标注实体ID（如“实体：产品A，ID：P001”），RAG可通过实体ID关联不同文档中的信息（如从“产品手册”获取功能，从“售后政策”获取保修期限）。
    
    #### 3. 降低大模型“上下文处理成本”
    RAG生成阶段需将“检索到的上下文”输入大模型，DOCRAY的结构化解析能减少大模型的“无效处理”：
    - 解析结果中的“实体标注、属性关联”可直接作为“结构化上下文”输入（如“产品A：重量5kg，价格1000元，适用场景：工业”），大模型无需从纯文本中二次提取关键信息，减少生成错误；
    - 对含表格/公式的文档，DOCRAY会将表格转化为“结构化文本描述”（如“表格1包含3列：产品名、重量、价格，其中产品A的重量为5kg，价格为1000元”），避免大模型因无法直接理解表格格式导致的信息遗漏。
    
    
    ### 三、功能扩展性：适配RAG系统的个性化需求
    DOCRAY支持灵活配置，可根据RAG的业务场景调整解析策略，避免“一刀切”的局限性：
    
    #### 1. 自定义解析规则：匹配业务文档特性
    不同行业的文档有独特结构（如医疗文档的“病例-诊断-处方”层级、法律文档的“法条-释义-案例”结构），DOCRAY支持：
    - 配置“解析模板”：按业务文档的固定格式定义拆分规则（如法律合同中，强制将“第一条 合同主体”拆分为独立语义块）；
    - 实体词典扩展：导入业务专属的实体词典（如制造业的“设备型号”“材料规格”），提升实体标注的准确率（避免将“型号X123”误标为普通文本）。
    
    #### 2. 与知识图谱协同：强化跨域关联能力
    若RAG系统已引入知识图谱（如前序对话中提及的跨知识库场景），DOCRAY可作为“知识图谱的数据源入口”：
    - 解析过程中提取的“实体-属性-关系”可直接同步至知识图谱（如将“产品A-价格-1000元”同步为图谱中的三元组）；
    - 反过来，知识图谱中的“实体关联关系”（如“产品A-适配配件-B”）也可指导DOCRAY的解析策略（如解析“配件手册”时，自动关联“产品A”的相关语义块），形成“解析-图谱-检索”的闭环。
    
    #### 3. 错误容忍与日志追溯：保障RAG可靠性
    RAG系统对“解析准确性”要求极高（解析错误会直接导致检索偏差），DOCRAY提供：
    - 解析质量校验：内置规则校验解析结果（如“合同文档必须包含‘有效期’实体，若缺失则标记异常”），避免无效信息进入RAG；
    - 完整日志记录：记录每篇文档的解析过程（如“拆分了多少语义块、标注了多少实体、异常节点位置”），方便RAG系统排查“检索偏差”的根源（如某问题检索不到结果，可追溯是否因解析时遗漏关键语义块）。
    
    
    ### 总结：DOCRAY在RAG中的定位
    DOCRAY并非“替代传统RAG的检索或生成模块”，而是作为**“前端信息预处理的核心工具”**，通过“强结构化解析”解决RAG系统中“信息碎片化、检索精度低、跨域关联难”的痛点。尤其在处理“大规模复杂业务文档”（如几千份产品手册、合同、政策文件）的RAG场景中，DOCRAY能显著降低后续检索和生成的成本，提升最终回答的准确性和可靠性——这与你此前关注的“跨分段/跨知识库问题处理”需求高度契合，可作为现有MASS平台RAG能力的重要补充。
    """
    def supported_extensions(self) -> list[str]:
        return SUPPORTED_EXTENSIONS

    def parse_file(self, path: Path, metadata: dict[str, Any], **kwargs) -> list[Part]:
        if not settings.docray_host:
            raise FallbackError("DOCRAY_HOST is not set")  # 本地启动没有配置docrag服务，触发异常。关于docrag服务请见D:\project\AI\ApeRAG\docker-compose.yml--services.docray

        job_id = None
        temp_dir_obj = None
        try:
            temp_dir_obj = tempfile.TemporaryDirectory()
            temp_dir_path = Path(temp_dir_obj.name)

            # Submit file to doc-ray
            with open(path, "rb") as f:
                files = {"file": (path.name, f)}
                response = requests.post(f"{settings.docray_host}/submit", files=files)
                response.raise_for_status()
                submit_response = response.json()
                job_id = submit_response["job_id"]
                logger.info(f"Submitted file {path.name} to DocRay, job_id: {job_id}")

            # Polling the processing status
            while True:
                time.sleep(5)  # Poll every 5 second
                status_response: dict = requests.get(f"{settings.docray_host}/status/{job_id}").json()
                status = status_response["status"]
                logger.info(f"DocRay job {job_id} status: {status}")

                if status == "completed":
                    break
                elif status == "failed":
                    error_message = status_response.get("error", "Unknown error")
                    raise RuntimeError(f"DocRay parsing failed for job {job_id}: {error_message}")
                elif status not in ["processing"]:
                    raise RuntimeError(f"Unexpected DocRay job status for {job_id}: {status}")

            # Get the result
            result_response = requests.get(f"{settings.docray_host}/result/{job_id}").json()
            result = result_response["result"]
            middle_json = result["middle_json"]
            images_data = result.get("images", {})

            # Dump image files into temp dir
            for img_name, img_base64 in images_data.items():
                img_file_path = temp_dir_path / str(img_name)

                # Ensure the resolved path is within the temporary directory.
                resolved_img_file_path = img_file_path.resolve()
                resolved_temp_dir_path = temp_dir_path.resolve()
                if not resolved_img_file_path.is_relative_to(resolved_temp_dir_path):
                    logger.error(
                        f"Security: Prevented writing image to an unintended path. "
                        f"File name: '{img_name}' "
                        f"Attempted path: '{resolved_img_file_path}', "
                        f"Temp dir: '{resolved_temp_dir_path}'"
                    )
                    continue

                img_file_path.parent.mkdir(parents=True, exist_ok=True)
                img_data = base64.b64decode(img_base64)
                with open(img_file_path, "wb") as f_img:
                    f_img.write(img_data)

            if metadata is None:
                metadata = {}
            parts = middle_json_to_parts(temp_dir_path / "images", middle_json, metadata)
            if not parts:
                return []

            pdf_data = result.get("pdf_data", None)
            if pdf_data:
                pdf_part = PdfPart(data=base64.b64decode(pdf_data), metadata=metadata.copy())
                parts.append(pdf_part)

            md_part = to_md_part(parts, metadata.copy())
            return [md_part] + parts

        except requests.exceptions.RequestException:
            logger.exception("DocRay API request failed")
            raise
        except Exception:
            logger.exception("DocRay parsing failed")
            raise
        finally:
            # Delete the job in doc-ray to release resources
            if job_id:
                try:
                    requests.delete(f"{settings.docray_host}/result/{job_id}")
                    logger.info(f"Deleted DocRay job {job_id}")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Failed to delete DocRay job {job_id}: {e}")
            if temp_dir_obj:
                temp_dir_obj.cleanup()
