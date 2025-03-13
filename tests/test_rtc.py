import asyncio
import pytest
import uuid

from getstream import Stream
from getstream.video.rtc.rtc import JoinError


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


@pytest.mark.skip_in_ci
@pytest.mark.asyncio
async def test_rtc_call_join_success(rtc_call):
    """
    Test successful RTC call joining.

    This test attempts to join a call with valid credentials and verifies that
    no exception is raised.
    """
    # Attempt to join the call with a short timeout
    await rtc_call.join("test-user", timeout=10.0)

    # If we got here, the join was successful
    assert rtc_call._joined is True


@pytest.mark.skip_in_ci
@pytest.mark.asyncio
async def test_rtc_call_join_failure():
    """
    Test failed RTC call joining with invalid credentials.

    This test attempts to join a call with invalid credentials and verifies that
    the appropriate exception is raised.
    """
    # Create a client with invalid credentials
    invalid_client = Stream(api_key="invalid_key", api_secret="invalid_secret")

    # Create a call with the invalid client
    invalid_call = invalid_client.video.rtc_call("default", str(uuid.uuid4()))

    # Attempt to join the call with a short timeout
    # This should raise a JoinError or a TimeoutError
    with pytest.raises((JoinError, asyncio.TimeoutError)):
        await invalid_call.join("test-user", timeout=10.0)
