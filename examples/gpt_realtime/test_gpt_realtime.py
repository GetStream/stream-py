import pytest
import pytest_asyncio
from gpt_realtime import GPTRealtime

@pytest_asyncio.fixture
async def gpt_realtime():
    """
    Fixture to initialize and clean up a GPTRealtime instance for testing.
    """
    gpt = GPTRealtime()
    await gpt.start_session()
    return gpt

@pytest.mark.asyncio
async def test_get_openai_token(gpt_realtime):
    """
    Test to ensure the OpenAI token is retrieved successfully.
    """
    token = gpt_realtime.get_openai_token()
    assert token is not None, "Token should not be None"

@pytest.mark.asyncio
async def test_send_text_message(gpt_realtime):
    """
    Test to ensure a text message is sent successfully.
    """
    try:
        await gpt_realtime.send_text_message("Test message")
        assert True, "Message sent successfully"
    except Exception as e:
        pytest.fail(f"Failed to send message: {e}")

@pytest.mark.asyncio
async def test_session_lifecycle():
    """
    Test to ensure the session lifecycle is managed correctly.
    """
    gpt = GPTRealtime()
    await gpt.start_session()
    assert gpt.dc is not None, "Data channel should be initialized"
    await gpt.stop_session()
    assert gpt.dc is None, "Data channel should be closed after stopping session"
