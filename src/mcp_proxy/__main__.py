import asyncio
import logging
import os
import typing as t

from . import run_sse_client

logging.basicConfig(level=logging.DEBUG)
SSE_URL: t.Final[str] = os.getenv("SSE_URL", "")

if not SSE_URL:
    raise ValueError("SSE_URL environment variable is not set")

asyncio.run(run_sse_client(SSE_URL))
