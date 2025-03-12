import asyncio
import pytest
import uuid


@pytest.fixture
def rtc_call(client):
    """Create an RTC call object."""
    return client.video.rtc_call("default", str(uuid.uuid4()))


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
