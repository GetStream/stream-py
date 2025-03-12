import asyncio
import pytest
import uuid

from getstream import Stream


@pytest.fixture
def rtc_client():
    """Create a Stream client with specific credentials for RTC testing."""
    return Stream(
        api_key="hd8szvscpxvd",
        api_secret="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWktcmVjb3JkZXIifQ.Ic1dVrjX_gbfb4IdO9lhvZteQi8Ki_w0AlCXUvwot8k",
    )


@pytest.fixture
def rtc_call(rtc_client):
    """Create an RTC call object."""
    return rtc_client.video.rtc_call("default", str(uuid.uuid4()))


@pytest.mark.asyncio
async def test_rtc_call_initialization(rtc_call):
    """
    Test basic RTC call initialization.

    This test simply verifies that we can initialize the SDK and create an RTC call object.
    Since there's not much to test at this stage, we just wait a few seconds to ensure
    no errors occur during initialization.
    """
    # Verify that the call object was created successfully
    assert rtc_call is not None
    assert rtc_call.call_type == "default"

    # Wait a few seconds to ensure no errors occur
    await asyncio.sleep(3)
