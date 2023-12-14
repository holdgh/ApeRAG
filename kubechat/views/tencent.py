import time

from ninja import Router
import redis.asyncio as redis

from config import settings

router = Router()

@router.get("/webhook/event")
async def callback(request, code, state):
    redis_client = redis.Redis.from_url(settings.MEMORY_REDIS_URL)
    await redis_client.set("tencent_code", code)
    await redis_client.expireat("tencent_code", int(time.time()) + 300)

