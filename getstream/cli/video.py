import click

from getstream.models import CallRequest
from getstream import Stream
import uuid
from getstream.video.call import Call
from getstream.cli.utils import pass_client


@click.group()
def video():
    pass


def create_call_command(name, method):
    # TODO: use reflection to create the correct command
    # inspect arguments and map them to a click option
    # scalar types should map to an option
    # lists of scalars should map to a multiple option
    # dict/object params should map to a string that we parse from json
    cmd = click.command(name=name)(method)
    video.add_command(cmd)


call_commands = {
    "get_call": {"method": Call.get},
    "delete_call": {"method": Call.delete},
}

_ = [
    create_call_command(name, command["method"])
    for name, command in call_commands.items()
]


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
