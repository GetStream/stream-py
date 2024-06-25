import click
import inspect
from getstream.models import CallRequest
from getstream import Stream
from getstream.stream_response import StreamResponse
import uuid
from getstream.video.call import Call
from getstream.video.client import VideoClient
from getstream.cli.utils import pass_client, json_option
import json
from typing import get_origin, get_args, Union

def get_type_name(annotation):
    """
    Get the name of a type
    """
    if hasattr(annotation, '__name__'):
        return annotation.__name__
    elif hasattr(annotation, '_name'):
        return annotation._name
    elif get_origin(annotation):
        origin = get_origin(annotation)
        args = get_args(annotation)
        if origin is Union and type(None) in args:
            # This is an Optional type
            return get_type_name(args[0])
        return f"{origin.__name__}[{', '.join(get_type_name(arg) for arg in args)}]"
    return str(annotation)


def parse_complex_type(value, annotation):
    """
    Parse a complex type from a JSON string
    """
    if isinstance(value, str):
        try:
            data_dict = json.loads(value)
            type_name = get_type_name(annotation)
            if type_name in globals():
                return globals()[type_name](**data_dict)
            else:
                return data_dict
        except json.JSONDecodeError:
            raise click.BadParameter(f"Invalid JSON for '{annotation}' parameter")
    return value

def create_call_command_from_method(name, method):
    @click.command(name=name)
    @click.option('--call-type', required=True, help='The type of the call')
    @click.option('--call-id', required=True, help='The ID of the call')
    @pass_client
    def cmd(client, call_type, call_id, **kwargs):
        call = client.video.call(call_type, call_id)

        # Parse complex types
        sig = inspect.signature(method)
        for param_name, param in sig.parameters.items():
            if param_name in kwargs:
                type_name = get_type_name(param.annotation)
                if type_name not in ['str', 'int', 'bool', 'list', 'dict']:
                    kwargs[param_name] = parse_complex_type(kwargs[param_name], param.annotation)

        result = getattr(call, name)(**kwargs)
        print_result(result)

    sig = inspect.signature(method)
    for param_name, param in sig.parameters.items():
        if param_name in ['self', 'call_type', 'call_id']:
            continue
        add_option_from_arg(cmd, param_name, param)

    return cmd

def create_command_from_method(name, method):
    @click.command(name=name)
    @pass_client
    def cmd(client, **kwargs):
        # Parse complex types
        sig = inspect.signature(method)
        for param_name, param in sig.parameters.items():
            if param_name in kwargs and param.annotation.__name__ not in ['str', 'int', 'bool', 'list', 'dict']:
                kwargs[param_name] = parse_complex_type(kwargs[param_name], param.annotation.__name__)

        result = getattr(client.video, name)(**kwargs)
        print_result(result)

    sig = inspect.signature(method)
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        add_option_from_arg(cmd, param_name, param)

    return cmd

def add_option_from_arg(cmd, param_name, param):
    if param.annotation == str:
        cmd = click.option(f'--{param_name}', type=str)(cmd)
    elif param.annotation == int:
        cmd = click.option(f'--{param_name}', type=int)(cmd)
    elif param.annotation == bool:
        cmd = click.option(f'--{param_name}', is_flag=True)(cmd)
    # TODO: improve this to handle more complex types
    elif param.annotation == list:
        cmd = click.option(f'--{param_name}', multiple=True)(cmd)
    elif param.annotation == dict:
        cmd = json_option(f'--{param_name}')(cmd)
    else:
        cmd = json_option(f'--{param_name}')(cmd)
    return cmd

def print_result(result):
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
    "get_or_create": {"method": Call.get_or_create},
    # Add more call commands as needed
}

# Define the video commands
video_commands = {
    "query_call_members": {"method": VideoClient.query_call_members},
    "query_call_stats": {"method": VideoClient.query_call_stats},
    "query_calls": {"method": VideoClient.query_calls},
    "list_call_types": {"method": VideoClient.list_call_types},
    "create_call_type": {"method": VideoClient.create_call_type},
    "delete_call_type": {"method": VideoClient.delete_call_type},
    "get_call_type": {"method": VideoClient.get_call_type},
    "update_call_type": {"method": VideoClient.update_call_type},
    "get_edges": {"method": VideoClient.get_edges},
    # Add more video commands as needed
}

# Create the commands
call_cmds = [create_call_command_from_method(name, command["method"]) for name, command in call_commands.items()]
video_cmds = [create_command_from_method(name, command["method"]) for name, command in video_commands.items()]


# Create a group for call commands
@click.group()
def call():
    """Commands for specific calls"""
    pass

for cmd in call_cmds:
    call.add_command(cmd)

# Add the commands to the CLI group
@click.group()
def video():
    """Video-related commands"""
    pass

video.add_command(call)

for cmd in video_cmds:
    video.add_command(cmd)

@click.command()
@click.option("--rtmp-user-id", default=f"{uuid.uuid4()}")
@pass_client
def rtmp_in_setup(client: Stream, rtmp_user_id: str):
    call = client.video.call("default", f"rtmp-in-{uuid.uuid4()}").get_or_create(
        data=CallRequest(
            created_by_id=rtmp_user_id,
        ),
    )
    print(f"RTMP URL: {call.data.call.ingress.rtmp.address}")
    print(
        f"RTMP Stream Token: {client.create_call_token(user_id=rtmp_user_id, call_cids=[call.data.call.cid])}"
    )
    print(f"React call link: https://pronto.getstream.io/join/{call.data.call.id}")


video.add_command(rtmp_in_setup)
