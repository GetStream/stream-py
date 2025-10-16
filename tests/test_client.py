from getstream import Stream
import pytest


def test_incorrect_client_throws_exception(monkeypatch):
    # Ensure env-based defaults are not used for this test
    monkeypatch.delenv("STREAM_API_KEY", raising=False)
    monkeypatch.delenv("STREAM_API_SECRET", raising=False)

    # Missing required api_key should raise ValueError during validation
    with pytest.raises(ValueError):
        Stream(api_secret="your_api_secret")

    with pytest.raises(ValueError):
        Stream(api_key="", api_secret="your_api_secret")

    # Missing required api_secret should raise ValueError during validation
    with pytest.raises(ValueError):
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


def test_client_does_not_raise_exception_without_tracer(client: Stream, monkeypatch):
    # Monkey patch _get_tracer to always return None
    from getstream.common import telemetry

    monkeypatch.setattr(telemetry, "_get_tracer", lambda: None)

    response = client.get_app()
    assert response.data is not None


def test_client_works_with_no_otel(client: Stream, monkeypatch):
    # Monkey patch _get_tracer to always return None
    from getstream.common import telemetry

    monkeypatch.setattr(telemetry, "_HAS_OTEL", False)

    response = client.get_app()
    assert response.data is not None
