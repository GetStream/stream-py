from getstream import Stream
import pytest


def test_incorrect_client_throws_exception():
    with pytest.raises(TypeError):
        Stream(api_secret="your_api_secret")

    with pytest.raises(ValueError):
        Stream(api_key="", api_secret="your_api_secret")

    with pytest.raises(TypeError):
        Stream(api_key="xxx")

    with pytest.raises(ValueError):
        Stream(api_key="xxx", api_secret="")

    with pytest.raises(ValueError):
        Stream(api_key="xxx", api_secret="xxx", timeout=-1)

    with pytest.raises(ValueError):
        Stream(api_key="xxx", api_secret="xxx", timeout="one")

    with pytest.raises(ValueError):
        Stream(api_key="xxx", api_secret="xxx", base_url="")

    with pytest.raises(ValueError):
        Stream(api_key="xxx", api_secret="xxx", base_url="somethingbad-!")

    with pytest.raises(ValueError):
        Stream(api_key="xxx", api_secret="xxx", base_url="ftp://example.com")

    with pytest.raises(ValueError):
        Stream(api_key="xxx", api_secret="xxx", base_url="ftp://example.com")
