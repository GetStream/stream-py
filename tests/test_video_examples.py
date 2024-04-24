def test_setup_client():
    from getstream import Stream

    client = Stream(api_key="your_api_key", api_secret="your_api_secret")
    assert isinstance(client, Stream)
    assert client.api_key == "your_api_key"
    assert client.api_secret == "your_api_secret"
    assert client.timeout == 6.0
