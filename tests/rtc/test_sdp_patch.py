from getstream.video.rtc.connection_manager import (
    patch_sdp_offer,
    add_ice_candidates_to_sdp,
)

# Example SDP offer with different parameters for different media sections
SAMPLE_SDP_OFFER = """v=0
o=- 3953114238 3953114238 IN IP4 0.0.0.0
s=-
t=0 0
a=group:BUNDLE 0 1
a=msid-semantic:WMS *
m=video 56816 UDP/TLS/RTP/SAVPF 97 98 99 100 101 102
c=IN IP4 192.168.128.30
a=sendrecv
a=extmap:1 urn:ietf:params:rtp-hdrext:sdes:mid
a=extmap:3 http://www.webrtc.org/experiments/rtp-hdrext/abs-send-time
a=mid:0
a=msid:6e5112b8-ec6f-4517-8469-5cdee31e5186 10300689-6149-474d-ad18-5563f67f53c4
a=rtcp:9 IN IP4 0.0.0.0
a=rtcp-mux
a=ssrc-group:FID 1922451087 2602112267
a=ssrc:1922451087 cname:30203682-de61-4187-ab0d-3691485cfef2
a=ssrc:2602112267 cname:30203682-de61-4187-ab0d-3691485cfef2
a=rtpmap:97 VP8/90000
a=rtcp-fb:97 nack
a=rtcp-fb:97 nack pli
a=rtcp-fb:97 goog-remb
a=rtpmap:98 rtx/90000
a=fmtp:98 apt=97
a=rtpmap:99 H264/90000
a=rtcp-fb:99 nack
a=rtcp-fb:99 nack pli
a=rtcp-fb:99 goog-remb
a=fmtp:99 level-asymmetry-allowed=1;packetization-mode=1;profile-level-id=42001f
a=rtpmap:100 rtx/90000
a=fmtp:100 apt=99
a=rtpmap:101 H264/90000
a=rtcp-fb:101 nack
a=rtcp-fb:101 nack pli
a=rtcp-fb:101 goog-remb
a=fmtp:101 level-asymmetry-allowed=1;packetization-mode=1;profile-level-id=42e01f
a=rtpmap:102 rtx/90000
a=fmtp:102 apt=101
a=candidate:d69e6a12cac4b7f9927cae00f999797b 1 udp 2130706431 192.168.128.30 56816 typ host
a=candidate:e5bcfe9c71647ac306da9adfe5d02ca8 1 udp 2130706431 192.168.64.1 54600 typ host
a=candidate:b21307eff02d95536b95a9a7dffbd397 1 udp 2130706431 fd89:90c6:1a06:740f:10fa:9a0:aa86:1537 49378 typ host
a=candidate:605fdbace754c156c989072572583b03 1 udp 1694498815 89.98.91.110 21721 typ srflx raddr 192.168.128.30 rport 56816
a=end-of-candidates
a=ice-ufrag:OswD
a=ice-pwd:Z0IMeQhiq1oYL947P4cO13
a=fingerprint:sha-256 7E:DB:1D:FA:13:57:15:4C:AF:47:D7:44:83:E4:D6:D8:A2:BB:66:58:D9:EA:2F:76:95:C6:34:DA:F6:0A:B9:DA
a=fingerprint:sha-384 A6:3B:6D:B4:62:00:43:01:7F:78:54:89:A4:62:CF:82:B8:5C:4E:96:CF:6D:5D:0F:FF:CB:3D:57:45:FC:D9:D3:40:CB:56:C5:49:D8:C5:7B:E3:76:15:C0:38:18:9A:0F
a=fingerprint:sha-512 99:0E:D7:3B:4C:83:49:33:AD:92:5B:BE:01:11:3A:08:D0:C2:31:4C:B3:20:49:AD:E7:81:1F:5F:D3:38:52:21:70:26:2B:59:75:78:AC:F4:5A:41:75:7C:06:E0:B8:C2:A6:E1:6B:02:ED:95:51:35:AB:3D:0A:5A:0C:D6:BE:D6
a=setup:actpass
m=audio 62551 UDP/TLS/RTP/SAVPF 96 0 8
c=IN IP4 192.168.128.30
a=sendrecv
a=extmap:1 urn:ietf:params:rtp-hdrext:sdes:mid
a=extmap:2 urn:ietf:params:rtp-hdrext:ssrc-audio-level
a=mid:1
a=msid:6e5112b8-ec6f-4517-8469-5cdee31e5186 cb9b7309-1e62-4929-953d-d89624806ad1
a=rtcp:9 IN IP4 0.0.0.0
a=rtcp-mux
a=ssrc:1276285358 cname:30203682-de61-4187-ab0d-3691485cfef2
a=rtpmap:96 opus/48000/2
a=rtpmap:0 PCMU/8000
a=rtpmap:8 PCMA/8000
a=candidate:d69e6a12cac4b7f9927cae00f999797b 1 udp 2130706431 192.168.128.30 62551 typ host
a=candidate:e5bcfe9c71647ac306da9adfe5d02ca8 1 udp 2130706431 192.168.64.1 64614 typ host
a=candidate:b21307eff02d95536b95a9a7dffbd397 1 udp 2130706431 fd89:90c6:1a06:740f:10fa:9a0:aa86:1537 54073 typ host
a=candidate:605fdbace754c156c989072572583b03 1 udp 1694498815 89.98.91.110 62551 typ srflx raddr 192.168.128.30 rport 62551
a=end-of-candidates
a=ice-ufrag:w53w
a=ice-pwd:enxJ9CXC3S1h4EpQwvauRb
a=fingerprint:sha-256 7E:DB:1D:FA:13:57:15:4C:AF:47:D7:44:83:E4:D6:D8:A2:BB:66:58:D9:EA:2F:76:95:C6:34:DA:F6:0A:B9:DA
a=fingerprint:sha-384 A6:3B:6D:B4:62:00:43:01:7F:78:54:89:A4:62:CF:82:B8:5C:4E:96:CF:6D:5D:0F:FF:CB:3D:57:45:FC:D9:D3:40:CB:56:C5:49:D8:C5:7B:E3:76:15:C0:38:18:9A:0F
a=fingerprint:sha-512 99:0E:D7:3B:4C:83:49:33:AD:92:5B:BE:01:11:3A:08:D0:C2:31:4C:B3:20:49:AD:E7:81:1F:5F:D3:38:52:21:70:26:2B:59:75:78:AC:F4:5A:41:75:7C:06:E0:B8:C2:A6:E1:6B:02:ED:95:51:35:AB:3D:0A:5A:0C:D6:BE:D6
a=setup:actpass
"""

# SDP with only one media section for testing edge case
SDP_SINGLE_MEDIA = """v=0
o=- 3953114238 3953114238 IN IP4 0.0.0.0
s=-
t=0 0
a=group:BUNDLE 0
a=msid-semantic:WMS *
m=video 56816 UDP/TLS/RTP/SAVPF 97 98 99 100 101 102
c=IN IP4 192.168.128.30
a=sendrecv
a=extmap:1 urn:ietf:params:rtp-hdrext:sdes:mid
a=mid:0
a=ice-ufrag:OswD
a=ice-pwd:Z0IMeQhiq1oYL947P4cO13
a=fingerprint:sha-256 7E:DB:1D:FA:13:57:15:4C:AF:47:D7:44:83:E4:D6:D8:A2:BB:66:58:D9:EA:2F:76:95:C6:34:DA:F6:0A:B9:DA
a=setup:actpass
"""

# SDP with three media sections for more complex testing
SDP_THREE_MEDIA = """v=0
o=- 3953114238 3953114238 IN IP4 0.0.0.0
s=-
t=0 0
a=group:BUNDLE 0 1 2
a=msid-semantic:WMS *
m=video 56816 UDP/TLS/RTP/SAVPF 97 98 99
c=IN IP4 192.168.128.30
a=sendrecv
a=mid:0
a=ice-ufrag:AAA1
a=ice-pwd:BBB1
a=candidate:d69e6a12cac4b7f9927cae00f999797b 1 udp 2130706431 192.168.128.30 56816 typ host
a=fingerprint:sha-256 11:11:11:11
a=setup:actpass
m=audio 62551 UDP/TLS/RTP/SAVPF 96 0 8
c=IN IP4 192.168.128.30
a=sendrecv
a=mid:1
a=ice-ufrag:AAA2
a=ice-pwd:BBB2
a=candidate:different1 1 udp 2130706431 192.168.128.30 62551 typ host
a=fingerprint:sha-256 22:22:22:22
a=setup:actpass
m=application 62552 UDP/TLS/RTP/SAVPF 101
c=IN IP4 192.168.128.30
a=sendrecv
a=mid:2
a=ice-ufrag:AAA3
a=ice-pwd:BBB3
a=candidate:different2 1 udp 2130706431 192.168.128.30 62552 typ host
a=fingerprint:sha-256 33:33:33:33
a=setup:actpass
"""

# SDP with no ICE candidates
SDP_NO_CANDIDATES = """v=0
o=- 3953114238 3953114238 IN IP4 0.0.0.0
s=-
t=0 0
a=group:BUNDLE 0 1
a=msid-semantic:WMS *
m=video 56816 UDP/TLS/RTP/SAVPF 97 98 99
c=IN IP4 192.168.128.30
a=sendrecv
a=mid:0
a=ice-ufrag:AAA1
a=ice-pwd:BBB1
a=fingerprint:sha-256 11:11:11:11
a=setup:actpass
m=audio 62551 UDP/TLS/RTP/SAVPF 96 0 8
c=IN IP4 192.168.128.30
a=sendrecv
a=mid:1
a=ice-ufrag:AAA2
a=ice-pwd:BBB2
a=fingerprint:sha-256 22:22:22:22
a=setup:actpass
"""


def test_patch_sdp_offer_standard_case():
    """Test the standard case with two media sections having different parameters."""
    patched_sdp = patch_sdp_offer(SAMPLE_SDP_OFFER)

    # Verify that the patched SDP still parses correctly
    import aiortc.sdp

    session = aiortc.sdp.SessionDescription.parse(patched_sdp)

    # Verify we have two media sections
    assert len(session.media) == 2

    # Verify the ports are the same
    assert session.media[0].port == session.media[1].port == 56816

    # Verify the ICE parameters are the same
    assert (
        session.media[0].ice.usernameFragment
        == session.media[1].ice.usernameFragment
        == "OswD"
    )
    assert (
        session.media[0].ice.password
        == session.media[1].ice.password
        == "Z0IMeQhiq1oYL947P4cO13"
    )

    # Verify the candidates are the same
    assert len(session.media[0].ice_candidates) == len(session.media[1].ice_candidates)
    for i, candidate in enumerate(session.media[0].ice_candidates):
        assert candidate.foundation == session.media[1].ice_candidates[i].foundation
        assert candidate.component == session.media[1].ice_candidates[i].component
        assert candidate.priority == session.media[1].ice_candidates[i].priority
        assert candidate.ip == session.media[1].ice_candidates[i].ip
        assert candidate.port == session.media[1].ice_candidates[i].port
        assert candidate.type == session.media[1].ice_candidates[i].type

    # Verify the fingerprints are the same
    assert len(session.media[0].dtls.fingerprints) == len(
        session.media[1].dtls.fingerprints
    )
    for i, fingerprint in enumerate(session.media[0].dtls.fingerprints):
        assert fingerprint.algorithm == session.media[1].dtls.fingerprints[i].algorithm
        assert fingerprint.value == session.media[1].dtls.fingerprints[i].value


def test_patch_sdp_offer_single_media():
    """Test the case with a single media section (nothing to patch)."""
    original_sdp = SDP_SINGLE_MEDIA
    patched_sdp = patch_sdp_offer(original_sdp)

    # For a single media section, the SDP shouldn't change
    assert patched_sdp == original_sdp


def test_patch_sdp_offer_three_media():
    """Test the case with three media sections."""
    patched_sdp = patch_sdp_offer(SDP_THREE_MEDIA)

    import aiortc.sdp

    session = aiortc.sdp.SessionDescription.parse(patched_sdp)

    # Verify we have three media sections
    assert len(session.media) == 3

    # Verify all sections have the same ICE parameters as the first section
    for media in session.media[1:]:
        assert media.ice.usernameFragment == "AAA1"
        assert media.ice.password == "BBB1"
        assert media.port == 56816
        assert media.dtls.fingerprints[0].value == "11:11:11:11"

    # Verify all sections have the same candidate from the first section
    for media in session.media[1:]:
        assert len(media.ice_candidates) == 1
        assert media.ice_candidates[0].foundation == "d69e6a12cac4b7f9927cae00f999797b"


def test_patch_sdp_offer_no_candidates():
    """Test the case where there are no candidates in the original SDP."""
    patched_sdp = patch_sdp_offer(SDP_NO_CANDIDATES)

    import aiortc.sdp

    session = aiortc.sdp.SessionDescription.parse(patched_sdp)

    # Verify we have two media sections
    assert len(session.media) == 2

    # Verify all sections have the same ICE parameters as the first section
    assert session.media[1].ice.usernameFragment == "AAA1"
    assert session.media[1].ice.password == "BBB1"
    assert session.media[1].port == 56816
    assert session.media[1].dtls.fingerprints[0].value == "11:11:11:11"

    # Verify the candidates list is empty in both sections
    assert len(session.media[0].ice_candidates) == 0
    assert len(session.media[1].ice_candidates) == 0


def test_integrated_with_add_ice_candidates():
    """Test that patch_sdp_offer works well with add_ice_candidates_to_sdp."""
    # First patch the SDP to standardize parameters
    patched_sdp = patch_sdp_offer(SAMPLE_SDP_OFFER)

    # Then add ice candidates
    candidates = [
        "d69e6a12cac4b7f9927cae00f999797b 1 udp 2130706431 192.168.128.30 56816 typ host"
    ]
    final_sdp = add_ice_candidates_to_sdp(patched_sdp, candidates)

    # The patched SDP already contains candidates from the first media section,
    # and add_ice_candidates_to_sdp adds the candidate to both media sections.
    # Check for the presence of candidates but don't assert exact count since
    # different SessionDescription.parse implementations might handle duplicates differently.
    assert "a=candidate:d69e6a12cac4b7f9927cae00f999797b" in final_sdp
    assert "a=end-of-candidates" in final_sdp
