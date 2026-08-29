import redis.asyncio as redis
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status

redis_client = redis.Redis(host="localhost", port=6379, db=0)

RATE_LIMIT = 10
TIME_WINDOW = 60  # secs


async def rate_limiter(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{ip}"

    current = await redis_client.incr(key)

    if current == 1:
        await redis_client.expire(key, TIME_WINDOW)

    if current > RATE_LIMIT:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests!"},
        )
    return await call_next(request)
