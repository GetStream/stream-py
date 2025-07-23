import json
import types
import warnings


class ConnectionManagerWrapper:
    """
    Wrapper for OpenAI's connection manager that adds error checking and better error messages.
    """

    def __init__(self, connection_manager, call_type, call_id):
        self.connection_manager = connection_manager
        self.first_message = True
        self._iterator = None
        self.call_type = call_type
        self.call_id = call_id

    async def __aenter__(self):
        self.connection = await self.connection_manager.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.connection_manager.__aexit__(exc_type, exc_val, exc_tb)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not hasattr(self, "connection"):
            raise RuntimeError(
                "Connection not established. Use 'async with' to establish the connection first."
            )

        try:
            # Use the recv method to get the next event
            event = await self.connection.recv()

            if self.first_message:
                self.first_message = False
                if hasattr(event, "type") and event.type == "error":
                    try:
                        error_json = json.dumps(
                            event.__dict__ if hasattr(event, "__dict__") else str(event)
                        )
                        raise Exception(error_json)
                    except TypeError:
                        # Handle case where event is not JSON serializable
                        error_message = (
                            f"Error with call type '{self.call_type}': {str(event)}"
                        )
                        raise Exception(error_message)

            return event
        except StopAsyncIteration:
            raise
        except Exception as e:
            # If it's our custom exception, re-raise it
            if isinstance(e, Exception) and str(e).startswith('{"'):
                raise
            # For any other exception, add context about the call type/id
            error_msg = f"Error with call type '{self.call_type}' (ID: {self.call_id}): {str(e)}"
            raise Exception(error_msg) from e

    # Forward all other attributes to the connection
    def __getattr__(self, name):
        if hasattr(self, "connection") and hasattr(self.connection, name):
            return getattr(self.connection, name)
        return getattr(self.connection_manager, name)


def import_openai():
    try:
        import openai
    except ImportError:
        raise ImportError(
            "failed to import openai, make sure to install this package like this: "
            "getstream[openai-realtime]"
        )
    return openai


def get_openai_realtime_client(openai_api_key: str, base_url: str):
    openai = import_openai()

    # ensure the client connects to Stream WS proxy
    client = openai.AsyncOpenAI(api_key=openai_api_key)

    if base_url.startswith("http://"):
        client.websocket_base_url = (
            f"{base_url.replace('http://', 'ws://')}/video/connect_agent"
        )
    if base_url.startswith("https://"):
        client.websocket_base_url = (
            f"{base_url.replace('https://', 'wss://')}/video/connect_agent"
        )

    # patch client.beta.realtime.connect
    patch_realtime_connect(client)
    return client


def patched_connection_manager_prepare_url(self):
    import httpx

    # Get the client attribute, which might have a different name in different versions
    client_attr = None
    for attr in dir(self):
        if attr.endswith("__client"):
            client_attr = attr
            break

    if not client_attr:
        raise RuntimeError(
            "Failed to patch OpenAI client: could not find client attribute on connection manager. "
            "The OpenAI SDK structure may have changed."
        )

    client = getattr(self, client_attr)

    if not hasattr(client, "websocket_base_url"):
        raise RuntimeError(
            "Failed to patch OpenAI client: client does not have websocket_base_url attribute. "
            "The OpenAI SDK structure may have changed."
        )

    return httpx.URL(client.websocket_base_url)


async def patched_recv(self):
    """
    Receive the next message from the connection and parses it into a `RealtimeServerEvent` object.

    Canceling this method is safe. There's no risk of losing data.
    """
    # Check if the connection has the expected methods
    if not hasattr(self, "recv_bytes") or not hasattr(self, "parse_event"):
        raise RuntimeError(
            "Failed to patch OpenAI client: connection object does not have expected methods. "
            "The OpenAI SDK structure may have changed."
        )

    try:
        # Try to import from the expected location
        from openai.types.beta.realtime.error_event import ErrorEvent
    except ImportError:
        # Create a simple class for type checking, but warn that the SDK structure might have changed
        warnings.warn(
            "Could not import ErrorEvent from openai.types.beta.realtime.error_event. "
            "The OpenAI SDK structure may have changed."
        )

        class ErrorEvent:
            pass

    zebytes = await self.recv_bytes()
    ev = self.parse_event(zebytes)
    if isinstance(ev, ErrorEvent) and ev.type != "error":
        return dict_to_class(json.loads(zebytes))
    return ev


def patch_realtime_connect(client):
    # Check if client has the expected structure
    if not hasattr(client, "beta") or not hasattr(client.beta, "realtime"):
        raise RuntimeError(
            "Failed to patch OpenAI client: client does not have beta.realtime. "
            "The OpenAI SDK structure may have changed."
        )

    # Try to patch the AsyncRealtimeConnection.recv method directly
    try:
        # First, try to import the AsyncRealtimeConnection class
        from openai.resources.beta.realtime.realtime import (  # type: ignore
            AsyncRealtimeConnection,
        )

        # Store the original recv method and replace it with our patched version
        if not hasattr(AsyncRealtimeConnection, "recv"):
            raise ImportError("AsyncRealtimeConnection does not have recv method")

        # Save the original method
        AsyncRealtimeConnection._original_recv = AsyncRealtimeConnection.recv

        # Replace with our patched version
        AsyncRealtimeConnection.recv = patched_recv
    except ImportError as e:
        warnings.warn(
            f"Could not directly patch AsyncRealtimeConnection.recv: {str(e)}. "
            "Will attempt to patch at runtime."
        )

    # Try to patch the connection manager's _prepare_url method
    try:
        from openai.resources.beta.realtime.realtime import (
            AsyncRealtimeConnectionManager,
        )

        if not hasattr(AsyncRealtimeConnectionManager, "_prepare_url"):
            # Look for methods that might be the prepare_url method
            prepare_url_candidates = [
                attr
                for attr in dir(AsyncRealtimeConnectionManager)
                if "prepare" in attr.lower() and "url" in attr.lower()
            ]

            if not prepare_url_candidates:
                raise ImportError(
                    "AsyncRealtimeConnectionManager does not have a method that prepares URLs"
                )

            # Use the first candidate
            prepare_url_method = prepare_url_candidates[0]
        else:
            prepare_url_method = "_prepare_url"

        # Save the original method
        AsyncRealtimeConnectionManager._original_prepare_url = getattr(
            AsyncRealtimeConnectionManager, prepare_url_method
        )

        # Replace with our patched version
        setattr(
            AsyncRealtimeConnectionManager,
            prepare_url_method,
            patched_connection_manager_prepare_url,
        )
    except ImportError as e:
        warnings.warn(
            f"Could not directly patch AsyncRealtimeConnectionManager._prepare_url: {str(e)}. "
            "Will attempt to patch at runtime."
        )

    # Monkey patch the __aenter__ method of AsyncRealtimeConnectionManager to patch the connection's recv method
    try:
        # First, try to import the AsyncRealtimeConnectionManager class
        from openai.resources.beta.realtime.realtime import (
            AsyncRealtimeConnectionManager,
        )

        # Store the original __aenter__ method
        original_aenter = AsyncRealtimeConnectionManager.__aenter__

        # Define a wrapper for __aenter__ that patches the connection's recv method
        async def patched_aenter(self):
            # Call the original method to get the connection
            connection = await original_aenter(self)

            # Patch the connection's recv method if it hasn't been patched already
            if hasattr(connection, "recv") and not hasattr(
                connection, "_original_recv"
            ):
                connection._original_recv = connection.recv
                connection.recv = types.MethodType(patched_recv, connection)

            return connection

        # Replace the __aenter__ method with our patched version
        AsyncRealtimeConnectionManager.__aenter__ = patched_aenter
    except (ImportError, AttributeError) as e:
        warnings.warn(
            f"Could not patch AsyncRealtimeConnectionManager.__aenter__: {str(e)}. "
            "The recv method may not be patched correctly."
        )


def dict_to_class(dictionary):
    """
    Convert a dictionary to a StreamEvent object with a nice string representation.

    Args:
        dictionary: The dictionary to convert.

    Returns:
        A StreamEvent object with properties from the dictionary.
    """

    class StreamEvent:
        def __init__(self, *args, **kwargs):
            pass

        def __repr__(self):
            # Get the type field if it exists, otherwise use "StreamEvent"
            event_type = getattr(self, "type", "StreamEvent")

            # Convert to CamelCase
            if event_type:
                # First handle dots by splitting and joining with nothing
                if "." in event_type:
                    parts = event_type.split(".")
                    # Convert each part to CamelCase
                    camel_parts = []
                    for part in parts:
                        if "_" in part:
                            # Convert snake_case to CamelCase
                            subparts = part.split("_")
                            camel_parts.append(
                                "".join(subpart.capitalize() for subpart in subparts)
                            )
                        else:
                            camel_parts.append(part.capitalize())
                    event_type = "".join(camel_parts)
                elif "_" in event_type:
                    # Convert snake_case to CamelCase
                    parts = event_type.split("_")
                    event_type = "".join(part.capitalize() for part in parts)
                else:
                    event_type = event_type.capitalize()
            else:
                event_type = "Stream"

            # Create the class name
            class_name = f"{event_type}Event"

            # Get all attributes that aren't methods or private
            attrs = {
                k: v
                for k, v in self.__dict__.items()
                if not k.startswith("_") and not callable(v)
            }

            # Format attributes as key=value pairs
            attrs_str = ", ".join(f"{k}={repr(v)}" for k, v in attrs.items())

            return f"{class_name}({attrs_str})"

    obj = StreamEvent()
    for key, value in dictionary.items():
        if isinstance(value, dict):
            value = dict_to_class(value)
        setattr(obj, key, value)

    return obj
