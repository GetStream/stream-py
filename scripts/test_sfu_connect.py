#!/usr/bin/env python3
"""
Utility script for testing SFU connection and retry behavior.

Connects to a call as a given user and logs each step of the connection
process — useful for verifying SFU assignment, retry on transient errors
(e.g. SFU_FULL), and reassignment via the coordinator.

Environment variables
---------------------
STREAM_API_KEY      — Stream API key (required)
STREAM_API_SECRET   — Stream API secret (required)
STREAM_BASE_URL     — Coordinator URL (default: Stream cloud).
                      Set to http://127.0.0.1:3030 for a local coordinator.
USER_ID             — User ID to join as (default: "test-user").
CALL_TYPE           — Call type (default: "default").
CALL_ID             — Call ID. If not set, a random UUID is generated.

Usage
-----
    # Connect via cloud coordinator
    STREAM_API_KEY=... STREAM_API_SECRET=... \\
        uv run --extra webrtc python scripts/test_sfu_connect.py

    # Connect via local coordinator
    STREAM_BASE_URL=http://127.0.0.1:3030 \\
        uv run --extra webrtc python scripts/test_sfu_connect.py
"""

import asyncio
import logging
import os
import uuid

from dotenv import load_dotenv

from getstream import AsyncStream
from getstream.models import CallRequest
from getstream.video.rtc import ConnectionManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run():
    base_url = os.getenv("STREAM_BASE_URL")
    user_id = os.getenv("USER_ID", "test-user")
    call_type = os.getenv("CALL_TYPE", "default")
    call_id = os.getenv("CALL_ID", str(uuid.uuid4()))

    logger.info("Configuration:")
    logger.info(f"  Coordinator: {base_url or 'cloud (default)'}")
    logger.info(f"  User:        {user_id}")
    logger.info(f"  Call:        {call_type}:{call_id}")

    client_kwargs = {}
    if base_url:
        client_kwargs["base_url"] = base_url

    client = AsyncStream(timeout=10.0, **client_kwargs)

    call = client.video.call(call_type, call_id)
    logger.info("Creating call...")
    await call.get_or_create(data=CallRequest(created_by_id=user_id))
    logger.info("Call created")

    cm = ConnectionManager(
        call=call,
        user_id=user_id,
        create=False,
    )

    logger.info("Connecting to SFU...")

    async with cm:
        join = cm.join_response
        if join and join.credentials:
            logger.info(f"Connected to SFU: {join.credentials.server.edge_name}")
            logger.info(f"  WS endpoint:  {join.credentials.server.ws_endpoint}")
        logger.info(f"  Session ID:   {cm.session_id}")

        logger.info("Holding connection for 3s...")
        await asyncio.sleep(3)

        logger.info("Leaving call")

    logger.info("Done")


if __name__ == "__main__":
    asyncio.run(run())
