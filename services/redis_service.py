import json
import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL")


class RedisService:
    def __init__(self):
        self.redis = aioredis.from_url(REDIS_URL, decode_responses=True)

    async def get(self, key: str):
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set(self, key: str, value, ex: int = 60):
        return await self.redis.set(key, json.dumps(value), ex=ex)

    async def delete(self, key: str):
        return await self.redis.delete(key)

    async def exists(self, key: str):
        return await self.redis.exists(key)


# Dependency to get the RedisService instance
async def get_redis_service() -> RedisService:
    return RedisService()
