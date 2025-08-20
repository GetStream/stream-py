import pytest
import os


@pytest.fixture(scope="session")
def assemblyai_api_key():
    """Get the AssemblyAI API key from environment variables."""
    api_key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not api_key:
        pytest.skip(
            "ASSEMBLYAI_API_KEY environment variable not set. Add it to your .env file."
        )
    return api_key


@pytest.fixture(scope="session")
def assemblyai_language():
    """Get the AssemblyAI language from environment variables."""
    return os.environ.get("ASSEMBLYAI_LANGUAGE", "en")


@pytest.fixture(scope="session")
def assemblyai_sample_rate():
    """Get the AssemblyAI sample rate from environment variables."""
    return int(os.environ.get("ASSEMBLYAI_SAMPLE_RATE", "48000"))
