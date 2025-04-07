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

import time

from ninja import Router

from aperag.chat.utils import get_async_redis_client

router = Router()

@router.get("/webhook/event")
async def callback(request, code, state):
    # restore user_id in state, to distinguish code of different users
    redis_client = get_async_redis_client()
    redirect_uri = str(request.url)

    await redis_client.set("tencent_code_" + state, code)
    await redis_client.set("tencent_redirect_uri_" + state, redirect_uri)
    await redis_client.expireat("tencent_code_" + state, int(time.time()) + 300)

