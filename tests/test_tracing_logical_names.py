def _setup_tracer():
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    exporter = InMemorySpanExporter()
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    else:
        tp = TracerProvider()
        tp.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(tp)
    return exporter


def test_chat_channel_span_name_and_endpoint():
    exporter = _setup_tracer()

    from getstream import Stream
    from getstream.models import ChannelInput
    import httpx

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={}, request=request)

    transport = httpx.MockTransport(handler)

    client = Stream(api_key="k", api_secret="s", base_url="http://test", timeout=1.0)
    chat = client.chat
    chat.client = httpx.Client(base_url=chat.base_url, transport=transport)

    channel = chat.channel("messaging", "123")
    channel.get_or_create(data=ChannelInput(created_by_id="user-x"))

    spans = exporter.get_finished_spans()
    assert spans, "no spans captured"
    s = spans[-1]
    assert s.name == "channel.get_or_create"
    assert s.attributes.get("stream.endpoint") == "channel.get_or_create"
    assert s.attributes.get("stream.channel_cid") == "messaging:123"
