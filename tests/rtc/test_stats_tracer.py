"""Tests for StatsTracer class."""

from dataclasses import dataclass

import pytest
from unittest.mock import MagicMock, AsyncMock


@dataclass
class MockStat:
    """Simple mock stat object with attributes."""

    type: str
    kind: str = ""
    packetsReceived: int = 0
    packetsSent: int = 0
    bytesReceived: int = 0
    bytesSent: int = 0
    timestamp: int = 0


class TestStatsTracerFiltering:
    """Tests for stat type filtering based on peer type."""

    @pytest.mark.asyncio
    async def test_subscriber_filters_outbound_rtp(self):
        """Subscriber should not include outbound-rtp stats."""
        from getstream.video.rtc.stats_tracer import StatsTracer

        mock_pc = MagicMock()
        mock_pc.getStats = AsyncMock(
            return_value={
                "inbound_1": MockStat(type="inbound-rtp", kind="audio", packetsReceived=100),
                "outbound_1": MockStat(type="outbound-rtp", kind="audio", packetsSent=0),
                "transport_1": MockStat(type="transport", bytesReceived=1000),
            }
        )
        mock_pc._RTCPeerConnection__iceTransports = set()

        tracer = StatsTracer(mock_pc, "subscriber")
        result = await tracer.get()

        stat_types = [v.get("type") for v in result.delta.values() if isinstance(v, dict)]
        assert "inbound-rtp" in stat_types
        assert "transport" in stat_types
        assert "outbound-rtp" not in stat_types

    @pytest.mark.asyncio
    async def test_publisher_filters_inbound_rtp(self):
        """Publisher should not include inbound-rtp stats."""
        from getstream.video.rtc.stats_tracer import StatsTracer

        mock_pc = MagicMock()
        mock_pc.getStats = AsyncMock(
            return_value={
                "outbound_1": MockStat(type="outbound-rtp", kind="video", packetsSent=500),
                "inbound_1": MockStat(type="inbound-rtp", kind="video", packetsReceived=0),
                "transport_1": MockStat(type="transport", bytesSent=5000),
            }
        )
        mock_pc._RTCPeerConnection__iceTransports = set()

        tracer = StatsTracer(mock_pc, "publisher")
        result = await tracer.get()

        stat_types = [v.get("type") for v in result.delta.values() if isinstance(v, dict)]
        assert "outbound-rtp" in stat_types
        assert "transport" in stat_types
        assert "inbound-rtp" not in stat_types


class TestDeltaCompression:
    """Tests for delta compression."""

    @pytest.mark.asyncio
    async def test_delta_only_includes_changed_values(self):
        """Delta compression should only include values that changed."""
        from getstream.video.rtc.stats_tracer import StatsTracer

        mock_pc = MagicMock()
        mock_pc._RTCPeerConnection__iceTransports = set()

        # First call - baseline stats
        mock_pc.getStats = AsyncMock(
            return_value={
                "stat_1": MockStat(
                    type="transport", bytesReceived=1000, bytesSent=500, timestamp=1000
                ),
            }
        )

        tracer = StatsTracer(mock_pc, "publisher")
        await tracer.get()  # First call establishes baseline

        # Second call - only bytesReceived changed
        mock_pc.getStats = AsyncMock(
            return_value={
                "stat_1": MockStat(
                    type="transport", bytesReceived=2000, bytesSent=500, timestamp=2000
                ),
            }
        )

        result = await tracer.get()

        # Delta should only contain changed values
        stat = result.delta.get("stat_1", {})
        assert "bytesReceived" in stat  # Changed
        assert "bytesSent" not in stat  # Unchanged, should be omitted
        assert stat.get("type") is None  # Type unchanged from first call


class TestICECandidateStats:
    """Tests for ICE candidate stats extraction using real aiortc."""

    @pytest.mark.asyncio
    async def test_ice_candidate_stats_with_real_local_pc(self):
        """Test ICE stats extraction with a real local aiortc RTCPeerConnection."""
        from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer
        from getstream.video.rtc.stats_tracer import StatsTracer

        # Create a real peer connection with STUN server
        config = RTCConfiguration(
            iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
        )
        pc = RTCPeerConnection(configuration=config)

        try:
            # Create an offer to trigger ICE gathering
            pc.addTransceiver("audio", direction="sendonly")
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)

            # Wait briefly for ICE gathering
            import asyncio

            await asyncio.sleep(0.5)

            # Create tracer and get stats
            tracer = StatsTracer(pc, "publisher")
            result = await tracer.get()

            # Check that we have local candidate stats (no pairs without remote peer)
            local_candidates = [
                k
                for k, v in result.delta.items()
                if isinstance(v, dict) and v.get("type") == "local-candidate"
            ]
            assert len(local_candidates) >= 1, "Should have at least one local candidate"

            # Verify local candidate structure
            if local_candidates:
                candidate = result.delta[local_candidates[0]]
                assert "address" in candidate
                assert "port" in candidate
                assert "protocol" in candidate
                assert "candidateType" in candidate
                assert "priority" in candidate

        finally:
            await pc.close()

    @pytest.mark.asyncio
    async def test_candidate_id_stability(self):
        """Test that candidate IDs are stable across calls."""
        from getstream.video.rtc.stats_tracer import StatsTracer
        from unittest.mock import MagicMock

        # Create mock candidate
        mock_candidate = MagicMock()
        mock_candidate.foundation = "1"
        mock_candidate.component = 1
        mock_candidate.ip = "192.168.1.1"
        mock_candidate.port = 12345

        mock_pc = MagicMock()
        tracer = StatsTracer(mock_pc, "publisher")

        # Generate ID twice - should be identical
        id1 = tracer._candidate_id(mock_candidate, 0)
        id2 = tracer._candidate_id(mock_candidate, 0)

        assert id1 == id2
        assert len(id1) == 8  # 8 hex chars

        # Different transport index should give different ID
        id3 = tracer._candidate_id(mock_candidate, 1)
        assert id3 != id1
