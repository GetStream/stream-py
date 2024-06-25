import click
import inspect
from getstream.models import CallRequest
from getstream import Stream
from getstream.stream_response import StreamResponse
import uuid
from getstream.video.call import Call
from getstream.video.client import VideoClient
from getstream.cli.utils import pass_client, json_option
from pprint import pprint
import json

def print_result(result):
    if isinstance(result, StreamResponse):
        # TODO: verbose mode
        # click.echo(f"Status Code: {result.status_code()}")
        # click.echo("Headers:")
        # for key, value in result.headers().items():
        #     click.echo(f"  {key}: {value}")
        click.echo("Data:")
        click.echo(json.dumps(result.data.to_dict(), indent=2, default=str))
        # rate_limits = result.rate_limit()
        # if rate_limits:
        #     click.echo("Rate Limits:")
        #     click.echo(f"  Limit: {rate_limits.limit}")
        #     click.echo(f"  Remaining: {rate_limits.remaining}")
        #     click.echo(f"  Reset: {rate_limits.reset}")
    else:
        click.echo(json.dumps(result, indent=2, default=str))

def create_call_command(name, method):
    @click.command(name=name)
    @click.option('--call-type', required=True, help='The type of the call')
    @click.option('--call-id', required=True, help='The ID of the call')
    @pass_client
    def cmd(client, call_type, call_id, **kwargs):
        call = client.video.call(call_type, call_id)
        result = getattr(call, name)(**kwargs)
        print_result(result)

    sig = inspect.signature(method)
    for param_name, param in sig.parameters.items():
        if param_name in ['self', 'call_type', 'call_id']:
            continue
        add_option(cmd, param_name, param)

    return cmd

def create_video_command(name, method):
    @click.command(name=name)
    @pass_client
    def cmd(client, **kwargs):
        result = getattr(client.video, name)(**kwargs)
        print_result(result)

    sig = inspect.signature(method)
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        add_option(cmd, param_name, param)

    return cmd

def add_option(cmd, param_name, param):
    if param.annotation == str:
        cmd = click.option(f'--{param_name}', type=str)(cmd)
    elif param.annotation == int:
        cmd = click.option(f'--{param_name}', type=int)(cmd)
    elif param.annotation == bool:
        cmd = click.option(f'--{param_name}', is_flag=True)(cmd)
    elif param.annotation == list:
        cmd = click.option(f'--{param_name}', multiple=True)(cmd)
    elif param.annotation == dict:
        cmd = json_option(f'--{param_name}')(cmd)
    else:
        # print param
        #print(f"Unsupported type: {param.annotation}")
        cmd = click.option(f'--{param_name}')(cmd)
    return cmd

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
call_cmds = [create_call_command(name, command["method"]) for name, command in call_commands.items()]
video_cmds = [create_video_command(name, command["method"]) for name, command in video_commands.items()]


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
