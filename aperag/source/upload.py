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

import shutil
from typing import Any, Dict, Iterator

from aperag.objectstore.base import get_object_store
from aperag.schema.view_models import CollectionConfig
from aperag.source.base import LocalDocument, RemoteDocument, Source
from aperag.source.utils import gen_temporary_file


class UploadSource(Source):
    def __init__(self, ctx: CollectionConfig):
        super().__init__(ctx)

    def scan_documents(self) -> Iterator[RemoteDocument]:
        return iter([])

    def prepare_document(self, name: str, metadata: Dict[str, Any]) -> LocalDocument:
        # -- 基于对象存储实例获取文件对象
        obj_path = metadata.get("object_path", "")
        if not obj_path:
            raise Exception("empty object path")
        obj_store = get_object_store()  # 获取对象存储实例【本地对象存储实例aperag.objectstore.local.Local】
        obj = obj_store.get(obj_path)  # 根据文件元数据中的对象路径，使用对象存储实例获取文件对象
        if obj is None:
            raise Exception(f"object '{obj_path}' is not found")
        # -- 将文件对象拷贝至临时文件，返回基于临时文件的LocalDocument实例
        with gen_temporary_file(name) as temp_file, obj:
            shutil.copyfileobj(obj, temp_file)
            filepath = temp_file.name
        metadata["name"] = name
        return LocalDocument(name=name, path=filepath, metadata=metadata)

    def sync_enabled(self):
        return False
