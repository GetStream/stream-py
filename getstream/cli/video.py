import click
import inspect
from getstream.models import CallRequest
from getstream import Stream
from getstream.stream_response import StreamResponse
import uuid
from getstream.video.call import Call
from getstream.video.client import VideoClient
from getstream.cli.utils import (
    pass_client,
    get_type_name,
    parse_complex_type,
    add_option_from_arg,
)
import json


def create_call_command_from_method(name, method):
    """
    Create a Click command for a call-specific method.

    This function dynamically creates a Click command based on a given call method.
    It includes options for call type and ID, and inspects the method's parameters
    to create corresponding Click options.

    Args:
        name (str): The name of the command to create.
        method (Callable): The call method to convert into a Click command.

    Returns:
        click.Command: A Click command that wraps the given call method.

    Example:
        >>> class Call:
        ...     def get(self, call_type: str, call_id: str):
        ...         pass
        >>> cmd = create_call_command_from_method('get', Call.get)
        >>> cmd.name
        'get'
        >>> [p.name for p in cmd.params if isinstance(p, click.Option)]
        ['call-type', 'call-id']
    """

    @click.command(name=name)
    @click.option("--call-type", required=True, help="The type of the call")
    @click.option("--call-id", required=True, help="The ID of the call")
    @pass_client
    def cmd(client, call_type, call_id, **kwargs):
        call = client.video.call(call_type, call_id)

        # Parse complex types and handle boolean flags
        sig = inspect.signature(method)
        parsed_kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name in kwargs:
                type_name = get_type_name(param.annotation)
                if type_name == "bool":
                    # For boolean flags, their presence means True
                    parsed_kwargs[param_name] = True
                elif type_name not in ["str", "int", "list"]:
                    parsed_kwargs[param_name] = parse_complex_type(
                        kwargs[param_name], param.annotation
                    )
                else:
                    parsed_kwargs[param_name] = kwargs[param_name]

        # Convert dashes to underscores for method name
        method_name = name.replace("-", "_")
        result = getattr(call, method_name)(**parsed_kwargs)
        print_result(result)

    sig = inspect.signature(method)
    for param_name, param in sig.parameters.items():
        if param_name in ["self", "call_type", "call_id"]:
            continue
        cmd = add_option_from_arg(cmd, param_name, param)

    return cmd


def create_command_from_method(name, method):
    """
    Create a Click command from a method.

    This function dynamically creates a Click command based on a given method.
    It inspects the method's parameters and creates corresponding Click options.

    Args:
        name (str): The name of the command to create.
        method (Callable): The method to convert into a Click command.

    Returns:
        click.Command: A Click command that wraps the given method.

    Example:
        >>> class VideoClient:
        ...     def query_calls(self, limit: int = 10):
        ...         pass
        >>> cmd = create_command_from_method('query_calls', VideoClient.query_calls)
        >>> cmd.name
        'query_calls'
        >>> [p.name for p in cmd.params if isinstance(p, click.Option)]
        ['limit']
    """

    @click.command(name=name)
    @pass_client
    def cmd(client, **kwargs):
        # Parse complex types
        sig = inspect.signature(method)
        for param_name, param in sig.parameters.items():
            if param_name in kwargs and param.annotation.__name__ not in [
                "str",
                "int",
                "bool",
                "list",
                "dict",
            ]:
                kwargs[param_name] = parse_complex_type(
                    kwargs[param_name], param.annotation.__name__
                )

        result = getattr(client.video, name)(**kwargs)
        print_result(result)

    sig = inspect.signature(method)
    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue
        add_option_from_arg(cmd, param_name, param)

    return cmd


def print_result(result):
    """
    Print the result of a command execution.

    This function handles different types of results and prints them
    in a formatted manner. It specifically handles StreamResponse objects
    and falls back to JSON serialization for other types.

    Args:
        result (Any): The result to print. Can be a StreamResponse or any JSON-serializable object.

    Example:
        >>> class MockResponse:
        ...     def __init__(self):
        ...         self.data = type('Data', (), {'to_dict': lambda: {'key': 'value'}})()
        >>> mock_result = MockResponse()
        >>> print_result(mock_result)
        Data:
        {
          "key": "value"
        }
    """
    if isinstance(result, StreamResponse):
        click.echo("Data:")
        click.echo(json.dumps(result.data.to_dict(), indent=2, default=str))
    else:
        click.echo(json.dumps(result, indent=2, default=str))


# Define the call commands
call_commands = {
    "get": {"method": Call.get},
    "update": {"method": Call.update},
    "delete": {"method": Call.delete},
    "get-or-create": {"method": Call.get_or_create},
    "block-user": {"method": Call.block_user},
    "unblock-user": {"method": Call.unblock_user},
    "send-event": {"method": Call.send_call_event},
    "mute-users": {"method": Call.mute_users},
    "update-user-permissions": {"method": Call.update_user_permissions},
    # Add more call commands as needed
}

# Define the video commands
video_commands = {
    "query-call-members": {"method": VideoClient.query_call_members},
    "query-call-stats": {"method": VideoClient.query_call_stats},
    "query-calls": {"method": VideoClient.query_calls},
    "list-call-types": {"method": VideoClient.list_call_types},
    "create-call-type": {"method": VideoClient.create_call_type},
    "delete-call-type": {"method": VideoClient.delete_call_type},
    "get-call-type": {"method": VideoClient.get_call_type},
    "update-call-type": {"method": VideoClient.update_call_type},
    "get-edges": {"method": VideoClient.get_edges},
    # Add more video commands as needed
}

# Create the commands
call_cmds = []
for name, command in call_commands.items():
    try:
        cmd = create_call_command_from_method(name, command["method"])
        if cmd is not None:
            call_cmds.append(cmd)
        else:
            print(f"Warning: Failed to create command for {name}")
    except Exception as e:
        print(f"Error creating command for {name}: {str(e)}")

video_cmds = []
for name, command in video_commands.items():
    try:
        cmd = create_command_from_method(name, command["method"])
        if cmd is not None:
            video_cmds.append(cmd)
        else:
            print(f"Warning: Failed to create command for {name}")
    except Exception as e:
        print(f"Error creating command for {name}: {str(e)}")


# Create a group for call commands
@click.group()
def call():
    """Commands for specific calls"""
    pass


for cmd in call_cmds:
    if cmd is not None:
        call.add_command(cmd)
    else:
        print(f"Warning: Skipping None command")


# Add the commands to the CLI group
@click.group()
def video():
    """Video-related commands"""
    pass


video.add_command(call)

for cmd in video_cmds:
    if cmd is not None:
        video.add_command(cmd)
    else:
        print(f"Warning: Skipping None command")


@click.command()
@click.option("--rtmp-user-id", default=f"{uuid.uuid4()}")
@pass_client
def rtmp_in_setup(client: Stream, rtmp_user_id: str):
    call = client.video.call("default", f"rtmp-in-{uuid.uuid4()}").get_or_create(
        data=CallRequest(
            created_by_id=rtmp_user_id,
        ),
    )
    viewer_call_token = client.create_call_token(
        user_id=f"viewer-test-{uuid.uuid4()}", call_cids=[call.data.call.cid]
    )
    rtmp_call_token = client.create_call_token(
        user_id=rtmp_user_id, call_cids=[call.data.call.cid]
    )
    print(f"RTMP URL: {call.data.call.ingress.rtmp.address}")
    print(f"RTMP Stream Token: {rtmp_call_token}")
    print(
        f"React call link: https://pronto.getstream.io/join/{call.data.call.id}?api_key={client.api_key}&token={viewer_call_token}"
    )
    print(f"""FFMPEG test command: \
ffmpeg -re -stream_loop 400 -i ./SampleVideo_1280x720_30mb.mp4 -c:v libx264 -preset veryfast -b:v 3000k \
-maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -g 50 -c:a aac -b:a 160k -ac 2 \
-f flv {call.data.call.ingress.rtmp.address}/{rtmp_call_token}""")


video.add_command(rtmp_in_setup)
