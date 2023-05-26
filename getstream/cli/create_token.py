import click
from getstream import Stream
from datetime import timedelta


@click.command()
@click.option("--api-key", required=True, help="Your API key.")
@click.option("--api-secret", required=True, help="Your API secret.")
@click.option("--user-id", required=False, help="User ID to generate the token for.")
@click.option(
    "--expiration",
    type=int,
    help="Token expiration time in seconds (e.g., 3600 for 1 hour).",
)
@click.option(
    "--channel-cids", type=str, help="Channel CIDs to generate the token for."
)
@click.option("--role", type=str, help="Role to generate the token for.")
@click.option("--call-cids", type=str, help="Call CIDs to generate the token for.")
def create_token(
    api_key, api_secret, user_id, expiration, channel_cids, role, call_cids
):
    """Generate a JWT token for a user."""
    client = Stream(api_key=api_key, api_secret=api_secret)
    expires_in = timedelta(seconds=expiration) if expiration else None
    ccids = channel_cids.split(",") if channel_cids else None
    cids = call_cids.split(",") if call_cids else None
    r = "admin" if role is None else role
    token = client.create_token(
        user_id, expiration=expires_in, channel_cids=ccids, role=r, call_cids=cids
    )

    click.echo(f"Generated token: {token}")


if __name__ == "__main__":
    create_token()
