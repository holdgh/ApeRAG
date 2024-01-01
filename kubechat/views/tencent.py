import time

import redis.asyncio as redis
from ninja import Router

from config import settings

router = Router()

@router.get("/webhook/event")
async def callback(request, code, state):
    # restore user_id in state, to distinguish code of different users
    redis_client = redis.Redis.from_url(settings.MEMORY_REDIS_URL)
    redirect_uri = str(request.url)

    await redis_client.set("tencent_code_" + state, code)
    await redis_client.set("tencent_redirect_uri_" + state, redirect_uri)
    await redis_client.expireat("tencent_code_" + state, int(time.time()) + 300)

