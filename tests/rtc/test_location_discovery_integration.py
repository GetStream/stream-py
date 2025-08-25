import logging

import pytest

from getstream.video.rtc.location_discovery import (
    FALLBACK_LOCATION_NAME,
    HTTPHintLocationDiscovery,
)


@pytest.mark.integration
def test_real_discovery():
    """Integration test that connects to the real Stream hint URL.

    This test requires network access and will make a real HTTP request.
    It's marked with integration to make it easy to exclude from regular test runs.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_location_discovery_integration")

    discovery = HTTPHintLocationDiscovery(logger=logger)
    location = discovery.discover()

    logger.info(f"Discovered location: {location}")

    assert location is not None
    assert len(location) == 3  # Should be a 3-character code


@pytest.mark.integration
def test_cached_discovery():
    """Test that the discovery is cached and only makes one HTTP request.

    This test requires network access and will make a real HTTP request.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_cached_discovery")

    discovery = HTTPHintLocationDiscovery(logger=logger)

    # First call - should make an HTTP request
    location1 = discovery.discover()
    assert location1 is not None
    assert len(location1) == 3

    # Second call - should use the cached value
    location2 = discovery.discover()
    assert location2 is not None
    assert len(location2) == 3

    # Both calls should return the same location
    assert location1 == location2

    logger.info(f"Cached discovery result: {location1}")


@pytest.mark.integration
def test_fallback_with_invalid_url():
    """Test that discovery falls back to the default location with an invalid URL.

    This test doesn't require network access since it should fail immediately.
    """
    discovery = HTTPHintLocationDiscovery(url="invalid://url.com")
    location = discovery.discover()

    assert location == FALLBACK_LOCATION_NAME
