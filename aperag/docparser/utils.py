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

import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote_plus

from aperag.docparser.base import AssetBinPart


def get_soffice_cmd() -> str | None:
    """
    1、shutil.which() 函数
    这是 Python 标准库 shutil 中的一个工具函数，作用是在系统的环境变量 PATH 所指定的目录中，查找指定程序（这里是 soffice）的可执行文件路径。
        如果找到该程序，返回其完整路径（例如 '/usr/bin/soffice' 或 'C:\\Program Files\\LibreOffice\\program\\soffice.exe'）；
        如果找不到，返回 None。

    2、"soffice" 是什么
    soffice 是 LibreOffice 或 OpenOffice 办公套件的命令行启动程序名称。通过它可以在命令行中操作 Office 文档（如转换格式、批量处理等）。

    3、实际用途
    这段代码通常用于检查系统是否安装了 LibreOffice/OpenOffice，以便后续通过命令行调用其功能（例如在 Python 中自动转换文档格式）。
    """
    return shutil.which("soffice")  # 查找系统中是否安装了 soffice 程序及其可执行文件路径


def convert_office_doc(input_path: Path, output_dir: Path, target_format: str) -> Path:  # 采用soffice程序将doc、ppt文件转化为docx、pptx文件
    soffice_cmd = get_soffice_cmd()
    if soffice_cmd is None:
        raise RuntimeError("soffice command not found")

    if not input_path.exists:
        raise FileNotFoundError(f"input file {input_path} not exist")

    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        soffice_cmd,
        "--headless",
        "--norestore",
        "--convert-to",
        target_format,
        "--outdir",
        str(output_dir),
        str(input_path),
    ]
    # subprocess.run() 会创建一个新的子进程来执行 cmd 命令，但主进程会阻塞等待该子进程执行完毕后才继续运行，属于同步执行。
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        raise RuntimeError(
            f'convert failed, cmd: "{" ".join(cmd)}", output: {process.stdout.decode()}, error: {process.stderr.decode()}'
        )

    return output_dir / f"{input_path.stem}.{target_format}"


def asset_bin_part_to_url(part: AssetBinPart) -> str:
    url = f"asset://{part.asset_id}"
    if part.mime_type:
        url += f"?mime_type={quote_plus(part.mime_type)}"
    return url


def extension_to_mime_type(extension: str) -> str:
    extension = extension.lower()
    if extension == ".pdf":
        return "application/pdf"
    elif extension == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif extension == ".xlsx":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif extension == ".pptx":
        return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    elif extension == ".epub":
        return "application/epub+zip"
    elif extension == ".jpg" or extension == ".jpeg":
        return "image/jpeg"
    elif extension == ".png":
        return "image/png"
    elif extension == ".gif":
        return "image/gif"
    elif extension == ".svg":
        return "image/svg+xml"
    elif extension == ".webp":
        return "image/webp"
    else:
        return "application/octet-stream"
