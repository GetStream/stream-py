def test_operation_name_decorator_sets_span_name():
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )
    from getstream.common.telemetry import operation_name
    from getstream.base import BaseClient
    import httpx

    exporter = InMemorySpanExporter()
    tp = TracerProvider()
    tp.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(tp)

    class Dummy(BaseClient):
        @operation_name("dummy.op")
        def do(self):
            return self.get("/ping")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={}, request=request)

    transport = httpx.MockTransport(handler)
    c = Dummy(api_key="k", base_url="http://t", token="t", timeout=1.0)
    c.client = httpx.Client(base_url=c.base_url, transport=transport)
    c.do()

    spans = exporter.get_finished_spans()
    assert spans and spans[-1].name == "dummy.op"
