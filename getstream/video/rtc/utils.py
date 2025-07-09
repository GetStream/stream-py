import webbrowser
from urllib.parse import urlencode


def open_browser(api_key: str, token: str, call_id: str) -> str:
    """
    Helper function to open browser with Stream call link.

    This utility function is useful for example projects and demos that need to
    provide a quick way for users to join a call via browser.

    Args:
        api_key: Stream API key
        token: JWT token for the user
        call_id: ID of the call

    Returns:
        The URL that was opened
    """
    base_url = "https://pronto.getstream.io/bare/join/"
    params = {"api_key": api_key, "token": token, "skip_lobby": "true"}

    url = f"{base_url}{call_id}?{urlencode(params)}"
    print(f"Opening browser to: {url}")

    try:
        webbrowser.open(url)
        print("Browser opened successfully!")
    except Exception as e:
        print(f"Failed to open browser: {e}")
        print(f"Please manually open this URL: {url}")

    return url
