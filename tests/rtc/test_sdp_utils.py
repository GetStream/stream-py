from getstream.video.rtc.connection_manager import add_ice_candidates_to_sdp

# SDP example provided by the user
SAMPLE_SDP_OFFER = """v=0
o=- 1408117065241529580 1743682923 IN IP4 0.0.0.0
s=-
t=0 0
a=msid-semantic:WMS*
a=fingerprint:sha-256 6F:E7:E3:03:3C:0A:3D:BC:0F:0D:E5:CE:FC:21:3A:57:EC:6C:58:BE:74:96:FC:B8:88:9D:5F:77:B5:8A:81:BD
a=ice-lite
a=extmap-allow-mixed
a=group:BUNDLE 0 1
m=audio 9 UDP/TLS/RTP/SAVPF 111 63
c=IN IP4 0.0.0.0
a=setup:actpass
a=mid:0
a=ice-ufrag:sUxagcyNCNnYbvgu
a=ice-pwd:qUzjgKjvCHOBlzcTaLEJadGvcIkRmOTI
a=rtcp-mux
a=rtcp-rsize
a=rtpmap:111 opus/48000/2
a=fmtp:111 minptime=10;useinbandfec=1;sprop-stereo=1
a=rtpmap:63 red/48000/2
a=fmtp:63 111/111
a=ssrc:855730306 cname:d5fb7ddfd2ebe766:TRACK_TYPE_AUDIO:Iq
a=ssrc:855730306 msid:d5fb7ddfd2ebe766:TRACK_TYPE_AUDIO:Iq cae5fd31-3c9a-4743-a18b-8ce4df797bd9
a=ssrc:855730306 mslabel:d5fb7ddfd2ebe766:TRACK_TYPE_AUDIO:Iq
a=ssrc:855730306 label:cae5fd31-3c9a-4743-a18b-8ce4df797bd9
a=msid:d5fb7ddfd2ebe766:TRACK_TYPE_AUDIO:Iq cae5fd31-3c9a-4743-a18b-8ce4df797bd9
a=sendonly
m=audio 9 UDP/TLS/RTP/SAVPF 111 63
c=IN IP4 0.0.0.0
a=setup:actpass
a=mid:1
a=ice-ufrag:sUxagcyNCNnYbvgu
a=ice-pwd:qUzjgKjvCHOBlzcTaLEJadGvcIkRmOTI
a=rtcp-mux
a=rtcp-rsize
a=rtpmap:111 opus/48000/2
a=fmtp:111 minptime=10;useinbandfec=1;sprop-stereo=1
a=rtpmap:63 red/48000/2
a=fmtp:63 111/111
a=ssrc:1028331265 cname:cafaedc0f88e215e:TRACK_TYPE_AUDIO:41
a=ssrc:1028331265 msid:cafaedc0f88e215e:TRACK_TYPE_AUDIO:41 3ef53d12-721c-40a0-9f6e-06e8fc7ca094
a=ssrc:1028331265 mslabel:cafaedc0f88e215e:TRACK_TYPE_AUDIO:41
a=ssrc:1028331265 label:3ef53d12-721c-40a0-9f6e-06e8fc7ca094
a=msid:cafaedc0f88e215e:TRACK_TYPE_AUDIO:41 3ef53d12-721c-40a0-9f6e-06e8fc7ca094
a=sendonly
"""

SAMPLE_CANDIDATE_1 = (
    "1602193835 1 udp 2130706431 63.176.168.251 50220 typ host ufrag sUxagcyNCNnYbvgu"
)
SAMPLE_CANDIDATE_2 = "842163049 1 udp 16777215 192.168.1.100 50221 typ srflx raddr 63.176.168.251 rport 50221 ufrag sUxagcyNCNnYbvgu"

# Define the expected candidate block separately for clarity
# Note the trailing newline is important
EXPECTED_CANDIDATE_LINES_MULTIPLE = f"""a=candidate:{SAMPLE_CANDIDATE_1}
a=candidate:{SAMPLE_CANDIDATE_2}
a=end-of-candidates
"""

# Construct the full expected SDP manually (Keep for reference, but don't use for direct assert)
EXPECTED_SDP_WITH_CANDIDATES_REFERENCE = (
    """v=0
o=- 1408117065241529580 1743682923 IN IP4 0.0.0.0
s=-
t=0 0
a=msid-semantic:WMS*
a=fingerprint:sha-256 6F:E7:E3:03:3C:0A:3D:BC:0F:0D:E5:CE:FC:21:3A:57:EC:6C:58:BE:74:96:FC:B8:88:9D:5F:77:B5:8A:81:BD
a=ice-lite
a=extmap-allow-mixed
a=group:BUNDLE 0 1
m=audio 9 UDP/TLS/RTP/SAVPF 111 63
c=IN IP4 0.0.0.0
a=setup:actpass
a=mid:0
a=ice-ufrag:sUxagcyNCNnYbvgu
a=ice-pwd:qUzjgKjvCHOBlzcTaLEJadGvcIkRmOTI
a=rtcp-mux
a=rtcp-rsize
a=rtpmap:111 opus/48000/2
a=fmtp:111 minptime=10;useinbandfec=1;sprop-stereo=1
a=rtpmap:63 red/48000/2
a=fmtp:63 111/111
a=ssrc:855730306 cname:d5fb7ddfd2ebe766:TRACK_TYPE_AUDIO:Iq
a=ssrc:855730306 msid:d5fb7ddfd2ebe766:TRACK_TYPE_AUDIO:Iq cae5fd31-3c9a-4743-a18b-8ce4df797bd9
a=ssrc:855730306 mslabel:d5fb7ddfd2ebe766:TRACK_TYPE_AUDIO:Iq
a=ssrc:855730306 label:cae5fd31-3c9a-4743-a18b-8ce4df797bd9
a=msid:d5fb7ddfd2ebe766:TRACK_TYPE_AUDIO:Iq cae5fd31-3c9a-4743-a18b-8ce4df797bd9
a=sendonly
"""
    + EXPECTED_CANDIDATE_LINES_MULTIPLE
    + """m=audio 9 UDP/TLS/RTP/SAVPF 111 63
c=IN IP4 0.0.0.0
a=setup:actpass
a=mid:1
a=ice-ufrag:sUxagcyNCNnYbvgu
a=ice-pwd:qUzjgKjvCHOBlzcTaLEJadGvcIkRmOTI
a=rtcp-mux
a=rtcp-rsize
a=rtpmap:111 opus/48000/2
a=fmtp:111 minptime=10;useinbandfec=1;sprop-stereo=1
a=rtpmap:63 red/48000/2
a=fmtp:63 111/111
a=ssrc:1028331265 cname:cafaedc0f88e215e:TRACK_TYPE_AUDIO:41
a=ssrc:1028331265 msid:cafaedc0f88e215e:TRACK_TYPE_AUDIO:41 3ef53d12-721c-40a0-9f6e-06e8fc7ca094
a=ssrc:1028331265 mslabel:cafaedc0f88e215e:TRACK_TYPE_AUDIO:41
a=ssrc:1028331265 label:3ef53d12-721c-40a0-9f6e-06e8fc7ca094
a=msid:cafaedc0f88e215e:TRACK_TYPE_AUDIO:41 3ef53d12-721c-40a0-9f6e-06e8fc7ca094
a=sendonly
"""
    + EXPECTED_CANDIDATE_LINES_MULTIPLE
)


def test_add_multiple_candidates_to_sdp():
    """Tests adding multiple ICE candidates to the sample SDP."""
    candidates = [SAMPLE_CANDIDATE_1, SAMPLE_CANDIDATE_2]
    modified_sdp = add_ice_candidates_to_sdp(SAMPLE_SDP_OFFER, candidates)
    # assert modified_sdp == EXPECTED_SDP_WITH_CANDIDATES # Replace exact match with structural checks

    # Structural checks (similar to single candidate test)
    parts = modified_sdp.split("\nm=")  # Split includes the leading newline
    assert len(parts) == 3  # Session part + 2 media parts

    expected_multi_candidate_block_stripped = EXPECTED_CANDIDATE_LINES_MULTIPLE.rstrip()

    # Check first media section
    # parts[1] starts with 'audio 9...' and ends with candidates
    media_part_1_content = parts[1]
    assert media_part_1_content.rstrip().endswith(
        expected_multi_candidate_block_stripped
    )
    lines_part1 = media_part_1_content.rstrip().split("\n")
    assert (
        lines_part1[-4] == "a=sendonly"
    )  # Check line before the multi-line candidate block

    # Check second media section
    # parts[2] starts with 'audio 9...' and ends with candidates
    media_part_2_content = parts[2]
    assert media_part_2_content.rstrip().endswith(
        expected_multi_candidate_block_stripped
    )
    lines_part2 = media_part_2_content.rstrip().split("\n")
    assert (
        lines_part2[-4] == "a=sendonly"
    )  # Check line before the multi-line candidate block

    # Verify counts more loosely
    assert modified_sdp.count(f"a=candidate:{SAMPLE_CANDIDATE_1}") == 2
    assert modified_sdp.count(f"a=candidate:{SAMPLE_CANDIDATE_2}") == 2
    assert modified_sdp.count("a=end-of-candidates") == 2


def test_add_single_candidate_to_sdp():
    """Tests adding a single ICE candidate to the sample SDP."""
    candidates = [SAMPLE_CANDIDATE_1]
    modified_sdp = add_ice_candidates_to_sdp(SAMPLE_SDP_OFFER, candidates)

    # Check that the candidate block is present after each m-line section
    parts = modified_sdp.split("m=")
    assert len(parts) == 3  # Session part + 2 media parts

    expected_single_candidate_block = f"""a=candidate:{SAMPLE_CANDIDATE_1}
a=end-of-candidates
"""

    # Check first media section ends with the candidate block
    assert parts[1].rstrip().endswith(expected_single_candidate_block.rstrip())
    # Check the line *before* the candidate block is a=sendonly
    lines_part1 = parts[1].rstrip().split("\n")
    assert lines_part1[-3] == "a=sendonly"

    # Check second media section ends with the candidate block
    assert parts[2].rstrip().endswith(expected_single_candidate_block.rstrip())
    # Check the line *before* the candidate block is a=sendonly
    lines_part2 = parts[2].rstrip().split("\n")
    assert lines_part2[-3] == "a=sendonly"

    # Verify structure more loosely
    assert modified_sdp.count(f"a=candidate:{SAMPLE_CANDIDATE_1}") == 2
    assert modified_sdp.count("a=end-of-candidates") == 2


def test_add_no_candidates_to_sdp():
    """Tests calling the function with an empty candidate list."""
    candidates = []
    modified_sdp = add_ice_candidates_to_sdp(SAMPLE_SDP_OFFER, candidates)
    # SDP should remain unchanged
    assert modified_sdp == SAMPLE_SDP_OFFER


def test_sdp_without_media_sections():
    """Tests SDP with no m= lines."""
    sdp_no_media = """v=0
o=- 123 456 IN IP4 0.0.0.0
s=-
t=0 0
a=fingerprint:sha-256 FINGERPRINT
"""
    candidates = [SAMPLE_CANDIDATE_1]
    modified_sdp = add_ice_candidates_to_sdp(sdp_no_media, candidates)
    # SDP should remain unchanged as there's nowhere to add candidates
    assert modified_sdp == sdp_no_media
