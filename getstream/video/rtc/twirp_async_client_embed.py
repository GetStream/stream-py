# -*- coding: utf-8 -*-
# Code copied directly from:
# https://github.com/verloop/twirpy/blob/main/twirp/async_client.py
# Embedded here as the library doesn't seem to ship it correctly.

import asyncio
import json
from typing import Optional
from urllib.parse import urljoin  # Import urljoin for cleaner URL combination

import aiohttp

# Assuming these modules exist within the installed twirp package
# or need to be embedded as well if they are also problematic.
# For now, assume they are available from the installed 'twirp' base.
from twirp import exceptions
from twirp import errors


class AsyncTwirpClient:
    def __init__(
        self, address: str, session: Optional[aiohttp.ClientSession] = None
    ) -> None:
        # Ensure address ends with a slash for urljoin to work correctly
        if not address.endswith("/"):
            address += "/"
        self._address = address
        self._session = session

    async def _make_request(
        self, *, url, ctx, request, response_obj, session=None, **kwargs
    ):
        headers = ctx.get_headers()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        kwargs["headers"]["Content-Type"] = "application/protobuf"

        if session is None:
            session = self._session

        _session_created = False
        if not isinstance(session, aiohttp.ClientSession):
            session = aiohttp.ClientSession()
            _session_created = True

        # Construct the full URL by joining the base address and the path
        # Remove leading slash from url path if present, as self._address ends with /
        full_url = urljoin(self._address, url.lstrip("/"))

        try:
            # Use the correctly constructed full_url
            async with await session.post(
                url=full_url, data=request.SerializeToString(), **kwargs
            ) as resp:
                if resp.status == 200:
                    response = response_obj()
                    response.ParseFromString(await resp.read())
                    return response
                try:
                    raise exceptions.TwirpServerException.from_json(await resp.json())
                except (aiohttp.ContentTypeError, json.JSONDecodeError):
                    raise exceptions.twirp_error_from_intermediary(
                        resp.status, resp.reason, resp.headers, await resp.text()
                    ) from None
        except asyncio.TimeoutError as e:
            raise exceptions.TwirpServerException(
                code=errors.Errors.DeadlineExceeded,
                message=str(e) or "request timeout",
                meta={"original_exception": e},
            )
        except aiohttp.ServerConnectionError as e:
            # This catches more connection-related errors like ClientConnectorError
            raise exceptions.TwirpServerException(
                code=errors.Errors.Unavailable,
                message=str(e),
                meta={"original_exception": e},
            )
        finally:
            # Close the session only if we created it internally
            if _session_created and session:
                await session.close()
