import click
from typing import Optional
from getstream import Stream
from getstream.cli.configure import configure, debug_config, debug_permissions, get_credentials, show_config
from getstream.cli.utils import pass_client
from getstream.cli.video import video
from getstream.stream import BASE_URL

@click.group()
@click.option("--profile", default='default', help="Configuration profile to use")
@click.option("--base-url", default=BASE_URL, show_default=True)
@click.option("--timeout", default=3.0, show_default=True)
@click.pass_context
def cli(ctx, profile, base_url, timeout):
    ctx.ensure_object(dict)
    api_key, api_secret, app_name = get_credentials(profile)
    if api_key is None or api_secret is None:
        click.echo(f"Error: Unable to load credentials for profile '{profile}'.")
        click.echo(f"Please run 'stream-cli configure' to set up your profile.")
        ctx.exit(1)
    ctx.obj["client"] = Stream(
        api_key=api_key, api_secret=api_secret, timeout=timeout, base_url=base_url
    )
    ctx.obj["app_name"] = app_name

@click.command()
@click.option("--user-id", required=True)
@click.option("--call-cid", multiple=True, default=None)
@click.option("--role", default=None)
@click.option("--exp-seconds", type=int, default=None)
@pass_client
def create_token(
    client: Stream,
    app_name: str,
    user_id: str,
    call_cid=None,
    role: Optional[str] = None,
    exp_seconds=None,
):
    if call_cid is not None and len(call_cid) > 0:
        print(
            client.create_call_token(
                user_id=user_id, call_cids=call_cid, role=role, expiration=exp_seconds
            )
        )
    else:
        print(client.create_call_token(user_id=user_id))

cli.add_command(debug_config)
cli.add_command(debug_permissions)
cli.add_command(configure)
cli.add_command(show_config)
cli.add_command(create_token)
cli.add_command(video)  # Add video command directly to the main CLI group

def main():
    cli(obj={})

if __name__ == "__main__":
    main()