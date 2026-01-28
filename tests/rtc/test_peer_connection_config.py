"""Tests for PeerConnectionManager ICE configuration."""

import aiortc
from unittest.mock import Mock

from getstream.video.rtc.peer_connection import PeerConnectionManager


class TestPeerConnectionConfig:
    """Tests for ICE server configuration conversion."""

    def _create_manager_with_credentials(self, ice_servers: list) -> PeerConnectionManager:
        """Create a PeerConnectionManager with mocked credentials."""
        mock_connection_manager = Mock()
        mock_connection_manager.join_response.credentials.ice_servers = ice_servers
        mock_connection_manager.join_response.credentials.server.edge_name = (
            "sfu-dpk-london-test.stream-io-video.com"
        )
        return PeerConnectionManager(mock_connection_manager)

    def test_build_rtc_configuration_with_turn_servers(self):
        """Should convert coordinator ICE servers to aiortc RTCConfiguration."""
        ice_servers = [
            {
                "urls": ["turn:sfu-test.stream-io-video.com:3478"],
                "username": "user123",
                "password": "secret456",
            },
            {
                "urls": ["turn:sfu-test.stream-io-video.com:3478?transport=tcp"],
                "username": "user123",
                "password": "secret456",
            },
        ]

        manager = self._create_manager_with_credentials(ice_servers)
        config = manager._build_rtc_configuration()

        assert isinstance(config, aiortc.RTCConfiguration)
        assert config.iceServers is not None
        assert len(config.iceServers) == 2
        assert config.bundlePolicy == aiortc.RTCBundlePolicy.MAX_BUNDLE

        # Check first server
        server = config.iceServers[0]
        assert server.urls == ["turn:sfu-test.stream-io-video.com:3478"]
        assert server.username == "user123"
        assert server.credential == "secret456"  # password -> credential

    def test_build_rtc_configuration_handles_credential_field(self):
        """Should accept 'credential' field as alternative to 'password'."""
        ice_servers = [
            {
                "urls": ["stun:stun.example.com:19302"],
                "username": "user",
                "credential": "cred",  # Using 'credential' instead of 'password'
            },
        ]

        manager = self._create_manager_with_credentials(ice_servers)
        config = manager._build_rtc_configuration()

        assert config.iceServers is not None
        assert config.iceServers[0].credential == "cred"

    def test_get_connection_config_format(self):
        """Should return dict matching JS SDK trace format."""
        ice_servers = [
            {
                "urls": ["turn:sfu-test.stream-io-video.com:3478"],
                "username": "user123",
                "password": "secret456",
            },
        ]

        manager = self._create_manager_with_credentials(ice_servers)
        config = manager._get_connection_config()

        # Should have url, bundlePolicy, and iceServers (matching JS SDK format)
        assert config["url"] == "sfu-dpk-london-test.stream-io-video.com"
        assert config["bundlePolicy"] == "max-bundle"
        assert "iceServers" in config

        # ICE servers should use 'credential' not 'password'
        server = config["iceServers"][0]
        assert server["urls"] == ["turn:sfu-test.stream-io-video.com:3478"]
        assert server["username"] == "user123"
        assert server["credential"] == "secret456"
        assert "password" not in server

    def test_get_connection_config_multiple_servers(self):
        """Should include all ICE servers in trace config."""
        ice_servers = [
            {"urls": ["turn:server1.com:3478"], "username": "u1", "password": "p1"},
            {"urls": ["turn:server2.com:3478"], "username": "u2", "password": "p2"},
            {"urls": ["turns:server3.com:443"], "username": "u3", "password": "p3"},
        ]

        manager = self._create_manager_with_credentials(ice_servers)
        config = manager._get_connection_config()

        assert len(config["iceServers"]) == 3
