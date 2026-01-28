"""Tests for StatsTracer class."""

import pytest
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer


class TestStatsTracer:
    """Integration tests for StatsTracer using real aiortc peer connections."""

    @pytest.mark.asyncio
    async def test_publisher_stats_collection(self):
        """Publisher stats should include RTP, codec, and ICE candidate stats with enhancements."""
        from getstream.video.rtc.stats_tracer import StatsTracer

        config = RTCConfiguration(
            iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
        )
        pc = RTCPeerConnection(configuration=config)

        try:
            # Add audio and video transceivers
            pc.addTransceiver("audio", direction="sendonly")
            pc.addTransceiver("video", direction="sendonly")
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)

            # Brief wait for ICE gathering
            import asyncio

            await asyncio.sleep(0.3)

            tracer = StatsTracer(pc, "publisher")
            result = await tracer.get()

            # Collect stats by type
            stats_by_type = {}
            for k, v in result.delta.items():
                if isinstance(v, dict) and "type" in v:
                    stat_type = v["type"]
                    stats_by_type.setdefault(stat_type, []).append(v)

            # Should have outbound-rtp for audio and video
            assert "outbound-rtp" in stats_by_type
            outbound = stats_by_type["outbound-rtp"]
            kinds = {s.get("kind") for s in outbound}
            assert "audio" in kinds
            assert "video" in kinds

            # Publisher should NOT have inbound-rtp (filtered)
            assert "inbound-rtp" not in stats_by_type

            # RTP stats should have mid, mediaType, codecId
            for rtp in outbound:
                assert "mid" in rtp
                assert rtp.get("mediaType") == rtp.get("kind")
                assert "codecId" in rtp
                # codecId should reference an existing codec entry
                assert rtp["codecId"] in result.delta

            # Should have codec entries
            assert "codec" in stats_by_type
            codec = stats_by_type["codec"][0]
            assert "payloadType" in codec
            assert "mimeType" in codec
            assert "clockRate" in codec
            assert codec.get("codecType") == "encode"

            # Should have local ICE candidates
            assert "local-candidate" in stats_by_type
            candidate = stats_by_type["local-candidate"][0]
            assert "address" in candidate
            assert "port" in candidate
            assert "protocol" in candidate

        finally:
            await pc.close()

    @pytest.mark.asyncio
    async def test_subscriber_filters_outbound_rtp(self):
        """Subscriber stats should filter out outbound-rtp but include codec stats."""
        from getstream.video.rtc.stats_tracer import StatsTracer

        pc = RTCPeerConnection()

        try:
            pc.addTransceiver("audio", direction="recvonly")
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)

            tracer = StatsTracer(pc, "subscriber")
            result = await tracer.get()

            stat_types = {
                v.get("type") for v in result.delta.values() if isinstance(v, dict)
            }
            # Subscriber shouldn't have outbound-rtp
            assert "outbound-rtp" not in stat_types
            # But should have codec stats (with decode type)
            assert "codec" in stat_types

            codec = next(
                v
                for v in result.delta.values()
                if isinstance(v, dict) and v.get("type") == "codec"
            )
            assert codec.get("codecType") == "decode"

        finally:
            await pc.close()
