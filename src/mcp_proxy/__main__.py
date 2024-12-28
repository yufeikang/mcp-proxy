import asyncio
import logging
import os
import typing as t

from . import run_sse_client

logging.basicConfig(level=logging.DEBUG)
SSE_URL: t.Final[str] = os.getenv("SSE_URL", "")
API_ACCESS_TOKEN: t.Final[str] = os.getenv("API_ACCESS_TOKEN", None)

if not SSE_URL:
    raise ValueError("SSE_URL environment variable is not set")


def main():
    asyncio.run(run_sse_client(SSE_URL, api_access_token=API_ACCESS_TOKEN))


if __name__ == "__main__":
    main()
