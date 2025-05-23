#!/usr/bin/env python3
"""
Simple test for the Deepgram STT transcription example.
This test validates basic functionality without requiring real API keys.
"""

import os
import tempfile
import unittest
from unittest.mock import patch
import sys

# Add the parent directory to the path to import main
sys.path.append(".")


class TestDeepgramTranscriptionExample(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Create a temporary .env file for testing
        self.temp_env = tempfile.NamedTemporaryFile(
            mode="w", suffix=".env", delete=False
        )
        self.temp_env.write("""
STREAM_API_KEY=test_api_key
STREAM_API_SECRET=test_api_secret
STREAM_BASE_URL=https://chat.stream-io-api.com/
DEEPGRAM_API_KEY=test_deepgram_key
""")
        self.temp_env.close()

        # Set environment variables
        os.environ["STREAM_API_KEY"] = "test_api_key"
        os.environ["STREAM_API_SECRET"] = "test_api_secret"
        os.environ["STREAM_BASE_URL"] = "https://chat.stream-io-api.com/"
        os.environ["DEEPGRAM_API_KEY"] = "test_deepgram_key"

    def tearDown(self):
        """Clean up test environment."""
        os.unlink(self.temp_env.name)

    def test_load_credentials(self):
        """Test that credentials can be loaded from environment."""
        from main import load_credentials

        api_key, api_secret, deepgram_key = load_credentials()

        self.assertEqual(api_key, "test_api_key")
        self.assertEqual(api_secret, "test_api_secret")
        self.assertEqual(deepgram_key, "test_deepgram_key")

    def test_load_credentials_missing(self):
        """Test that missing credentials raise appropriate errors."""
        from main import load_credentials

        # Test missing STREAM_API_KEY
        del os.environ["STREAM_API_KEY"]
        with self.assertRaises(ValueError) as context:
            load_credentials()
        self.assertIn("STREAM_API_KEY", str(context.exception))

    def test_open_browser_url_construction(self):
        """Test that the browser URL is constructed correctly."""
        from main import open_browser

        with patch("webbrowser.open") as mock_open:
            url = open_browser("test_key", "test_token")

            expected_url = "https://pronto.getstream.io/bare/join/?api_key=test_key&token=test_token"
            self.assertEqual(url, expected_url)
            mock_open.assert_called_once_with(expected_url)

    def test_imports(self):
        """Test that all required imports work."""
        try:
            import main

            # Test that the main module can be imported without errors
            self.assertTrue(hasattr(main, "main"))
            self.assertTrue(hasattr(main, "load_credentials"))
            self.assertTrue(hasattr(main, "open_browser"))
        except ImportError as e:
            self.fail(f"Import failed: {e}")


if __name__ == "__main__":
    print("Running basic tests for Deepgram STT transcription example...")
    unittest.main(verbosity=2)
