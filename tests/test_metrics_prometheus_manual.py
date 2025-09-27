import time
import uuid
import pytest
from getstream import Stream
import urllib.request
from getstream.base import StreamAPIException


@pytest.mark.integration
def test_metrics_prometheus_manual(client: Stream):
    """
    Manual metrics check with Prometheus (real API calls).

    This test configures an in-process Prometheus exporter and serves metrics
    on http://localhost:9464/metrics. It then performs a few Stream API calls
    (both success and intentional failures) so you can inspect exported
    metrics in Prometheus format.

    Prerequisites:
    - Set Stream credentials in your environment (or .env)
      export STREAM_API_KEY=xxxx
      export STREAM_API_SECRET=yyyy
      # Optional (defaults to production): export STREAM_BASE_URL=https://chat.stream-io-api.com/

    - Install deps:
      pip install getstream[telemetry] opentelemetry-exporter-prometheus prometheus_client

    Run locally:
      uv run pytest -q -k metrics_prometheus_manual -s

    Inspect metrics:
      curl http://localhost:9464/metrics | rg getstream_client_request
      # or open in a browser: http://localhost:9464/metrics

    Notes:
    - Metric names exposed by this SDK:
        getstream.client.request.duration (histogram)
        getstream.client.request.count (counter)
      Prometheus exporter renders them as:
        getstream_client_request_duration_* and getstream_client_request_count_total
    - Attributes like stream.endpoint, http.response.status_code, and
      stream.call_cid/stream.channel_cid (when present) appear as labels.
    """

    try:
        from opentelemetry import metrics
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.exporter.prometheus import PrometheusMetricReader
        from prometheus_client import start_http_server
    except ImportError:
        pytest.skip(
            "Missing Prometheus exporter; install: pip install getstream[telemetry] opentelemetry-exporter-prometheus prometheus_client"
        )
        return

    # Start Prometheus exporter on :9464
    resource = Resource.create(
        {
            "service.name": "getstream-metrics-manual",
        }
    )
    reader = PrometheusMetricReader()
    metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=[reader])
    )
    start_http_server(port=9464)

    # Make a few calls — some will succeed, some fail — to populate metrics
    # Success (read-only)
    try:
        client.get_app()
        client.video.list_call_types()
        client.block_users(blocked_user_id="nonexistent", user_id="nonexistent")
        client.delete_users(
            user_ids=[f"manual-{uuid.uuid4().hex[:8]}"], messages="hard"
        )
    except StreamAPIException:
        pass

    # Fetch metrics via HTTP and assert our metric names are present

    metrics_url = "http://localhost:9464/metrics"
    print("Prometheus metrics available at:", metrics_url)

    def _get_metrics_text() -> str:
        with urllib.request.urlopen(metrics_url, timeout=5) as resp:
            return resp.read().decode("utf-8", errors="ignore")

    found = False
    deadline = time.time() + 10
    while time.time() < deadline and not found:
        text = _get_metrics_text()
        if (
            "getstream_client_request_count_total" in text
            or "getstream_client_request_duration_count" in text
        ):
            found = True
            break
        time.sleep(0.5)

    assert found, "Expected getstream metrics not found in Prometheus /metrics output"
