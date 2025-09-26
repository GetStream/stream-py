import os
import uuid
import pytest
from getstream import Stream
from models import ChannelInput, CallRequest


@pytest.mark.integration
def test_tracing_with_jaeger_manual(client: Stream):
    """
    Manual tracing check with Jaeger (no real API calls).

    This test configures OTLP exporters to a local Jaeger all-in-one and
    exercises both Video and Chat clients with a mix of successful and
    failing requests under mocked HTTP transports.

    How to run Jaeger locally:

    1) Start Jaeger (OTLP enabled):
       docker run --rm -it \
         -e COLLECTOR_OTLP_ENABLED=true \
         -p 16686:16686 -p 4317:4317 -p 4318:4318 \
         jaegertracing/all-in-one:1.51

    2) uv run pytest -q -k tracing_with_jaeger_manual -s

    3) Open the Jaeger UI:
       http://localhost:16686
    """

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
    except ImportError:
        pytest.skip("Missing OTel OTLP exporters")
        return

    # Configure Jaeger OTLP exporter
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
    resource = Resource.create(
        {
            "service.name": "getstream-manual-jaeger",
            "deployment.environment": "dev",
        }
    )
    tp = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)

    tp.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(tp)

    with trace.get_tracer("jaeger.test").start_as_current_span("start"):
        user_id = str(uuid.uuid4())
        client.create_user(name=user_id, id=user_id)

        channel = client.chat.channel("messaging", "123")
        channel.get_or_create(data=ChannelInput(created_by_id=user_id))

        call = client.video.call("default", "123")
        call.get_or_create(data=CallRequest(created_by_id=user_id))

    tp.force_flush(timeout_millis=2000)
