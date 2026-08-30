import time
import logging
from fastapi import Request

logger=logging.getLogger(__name__)

async def logging_middleware(request:Request, call_next):
    start_tiime=time.time()
    response= await call_next(request)
    duration=time.time()-start_tiime
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    return response