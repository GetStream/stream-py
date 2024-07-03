import click
from dotenv import load_dotenv
from typing import Optional
from getstream import Stream
from getstream.cli.utils import pass_client
from getstream.cli.video import video
from getstream.stream import BASE_URL


@click.group()
@click.option("--api-key")
@click.option("--api-secret")
@click.option("--base-url", default=BASE_URL, show_default=True)
@click.option("--timeout", default=3.0, show_default=True)
@click.pass_context
def cli(ctx: click.Context, api_key: str, api_secret: str, base_url: str, timeout=3.0):
    ctx.ensure_object(dict)
    ctx.obj["client"] = Stream(
        api_key=api_key, api_secret=api_secret, timeout=timeout, base_url=base_url
    )


@click.command()
@click.option("--user-id", required=True)
@click.option("--call-cid", multiple=True, default=None)
@click.option("--role", default=None)
@click.option("--exp-seconds", type=int, default=None)
@pass_client
def create_token(
    client: Stream, user_id: str, call_cid=None,  role: Optional[str] = None, exp_seconds=None
):
    if call_cid is not None and len(call_cid) > 0:
        print(
            client.create_call_token(
                user_id=user_id, call_cids=call_cid, role=role, expiration=exp_seconds
            )
        )
    else:
        print(client.create_call_token(user_id=user_id))


cli.add_command(create_token)
cli.add_command(video)
#cli.add_command(chat)

def main():
    load_dotenv()
    cli(auto_envvar_prefix="STREAM", obj={})


if __name__ == "__main__":
    main()
