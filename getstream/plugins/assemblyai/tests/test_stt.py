import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, AsyncMock

# Don't import AssemblyAISTT at module level to avoid import issues during test collection
# from getstream.plugins.assemblyai import AssemblyAISTT
from getstream.video.rtc.track_util import PcmData


class TestAssemblyAISTT:
    """Test cases for AssemblyAI STT plugin."""

    def test_import_success(self):
        """Test that the plugin can be imported successfully."""
        from getstream.plugins.assemblyai import AssemblyAISTT
        assert AssemblyAISTT is not None

    def test_init_with_api_key(self, assemblyai_api_key):
        """Test initialization with API key."""
        with patch('getstream.plugins.assemblyai.stt.stt._assemblyai_available', True), \
             patch('getstream.plugins.assemblyai.stt.stt.aai') as mock_aai, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClient') as mock_streaming_client, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClientOptions') as mock_options, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingEvents') as mock_events, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingParameters') as mock_params:
            mock_aai.settings.api_key = "test_key"
            mock_streaming_client.return_value = Mock()
            mock_options.return_value = Mock()
            mock_events.Begin = Mock()
            mock_events.Turn = Mock()
            mock_events.Termination = Mock()
            mock_events.Error = Mock()
            mock_params.return_value = Mock()
            from getstream.plugins.assemblyai import AssemblyAISTT
            stt = AssemblyAISTT(api_key=assemblyai_api_key)
            assert stt.sample_rate == 48000
            assert stt.language == "en"
            assert stt.interim_results is True
            assert stt.enable_partials is True
            assert stt.enable_automatic_punctuation is True
            assert stt.enable_utterance_end_detection is True

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        with patch('getstream.plugins.assemblyai.stt.stt._assemblyai_available', True), \
             patch('getstream.plugins.assemblyai.stt.stt.aai') as mock_aai, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClient') as mock_streaming_client, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClientOptions') as mock_options, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingEvents') as mock_events, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingParameters') as mock_params:
            mock_aai.settings.api_key = "test_key"
            mock_streaming_client.return_value = Mock()
            mock_options.return_value = Mock()
            mock_events.Begin = Mock()
            mock_events.Turn = Mock()
            mock_events.Termination = Mock()
            mock_events.Error = Mock()
            mock_params.return_value = Mock()
            from getstream.plugins.assemblyai import AssemblyAISTT
            stt = AssemblyAISTT(
                sample_rate=16000,
                language="es",
                interim_results=False,
                enable_partials=False,
                enable_automatic_punctuation=False,
                enable_utterance_end_detection=False,
            )
            assert stt.sample_rate == 16000
            assert stt.language == "es"
            assert stt.interim_results is False
            assert stt.enable_partials is False
            assert stt.enable_automatic_punctuation is False
            assert stt.enable_utterance_end_detection is False

    def test_init_without_api_key_logs_warning(self):
        """Test that initialization without API key logs a warning."""
        with patch('getstream.plugins.assemblyai.stt.stt._assemblyai_available', True), \
             patch('getstream.plugins.assemblyai.stt.stt.aai') as mock_aai, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClient') as mock_streaming_client, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClientOptions') as mock_options, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingEvents') as mock_events, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingParameters') as mock_params:
            mock_aai.settings.api_key = "test_key"
            mock_streaming_client.return_value = Mock()
            mock_options.return_value = Mock()
            mock_events.Begin = Mock()
            mock_events.Turn = Mock()
            mock_events.Termination = Mock()
            mock_events.Error = Mock()
            mock_params.return_value = Mock()
            from getstream.plugins.assemblyai import AssemblyAISTT
            
            with patch('getstream.plugins.assemblyai.stt.stt.logger') as mock_logger:
                stt = AssemblyAISTT()
                # Should still initialize but with warning
                assert stt is not None
                # Check that warning was logged
                mock_logger.warning.assert_called_with(
                    "No API key provided and ASSEMBLYAI_API_KEY environment variable not found."
                )

    @pytest.mark.asyncio
    async def test_close_method(self, assemblyai_api_key):
        """Test that the close method works correctly."""
        with patch('getstream.plugins.assemblyai.stt.stt._assemblyai_available', True), \
             patch('getstream.plugins.assemblyai.stt.stt.aai') as mock_aai, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClient') as mock_streaming_client, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClientOptions') as mock_options, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingEvents') as mock_events, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingParameters') as mock_params:
            mock_aai.settings.api_key = "test_key"
            mock_streaming_client.return_value = Mock()
            mock_options.return_value = Mock()
            mock_events.Begin = Mock()
            mock_events.Turn = Mock()
            mock_events.Termination = Mock()
            mock_events.Error = Mock()
            mock_params.return_value = Mock()
            from getstream.plugins.assemblyai import AssemblyAISTT
            stt = AssemblyAISTT(api_key=assemblyai_api_key)
            
            # Mock the streaming client
            stt.streaming_client = Mock()
            stt.streaming_client.disconnect = Mock()
            
            await stt.close()
            
            assert stt._is_closed is True
            assert stt._running is False
            stt.streaming_client.disconnect.assert_called_once()

    def test_pcm_data_validation(self, assemblyai_api_key):
        """Test that PCM data validation works correctly."""
        with patch('getstream.plugins.assemblyai.stt.stt._assemblyai_available', True), \
             patch('getstream.plugins.assemblyai.stt.stt.aai') as mock_aai, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClient') as mock_streaming_client, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClientOptions') as mock_options, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingEvents') as mock_events, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingParameters') as mock_params:
            mock_aai.settings.api_key = "test_key"
            mock_streaming_client.return_value = Mock()
            mock_options.return_value = Mock()
            mock_events.Begin = Mock()
            mock_events.Turn = Mock()
            mock_events.Termination = Mock()
            mock_events.Error = Mock()
            mock_params.return_value = Mock()
            from getstream.plugins.assemblyai import AssemblyAISTT
            stt = AssemblyAISTT(api_key=assemblyai_api_key)
            
            # Create test PCM data
            samples = np.array([1000, -1000, 500, -500], dtype=np.int16)
            pcm_data = PcmData(samples=samples, sample_rate=48000)
            
            # Should not raise an exception
            assert pcm_data.samples is not None
            assert pcm_data.sample_rate == 48000

    @pytest.mark.asyncio
    async def test_process_audio_sample_rate_mismatch(self, assemblyai_api_key):
        """Test that sample rate mismatch warning is logged."""
        with patch('getstream.plugins.assemblyai.stt.stt._assemblyai_available', True), \
             patch('getstream.plugins.assemblyai.stt.stt.aai') as mock_aai, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClient') as mock_streaming_client, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClientOptions') as mock_options, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingEvents') as mock_events, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingParameters') as mock_params:
            mock_aai.settings.api_key = "test_key"
            mock_streaming_client.return_value = Mock()
            mock_options.return_value = Mock()
            mock_events.Begin = Mock()
            mock_events.Turn = Mock()
            mock_events.Termination = Mock()
            mock_events.Error = Mock()
            mock_params.return_value = Mock()
            from getstream.plugins.assemblyai import AssemblyAISTT
            stt = AssemblyAISTT(api_key=assemblyai_api_key, sample_rate=48000)
            
            # Create PCM data with different sample rate
            samples = np.array([1000, -1000, 500, -500], dtype=np.int16)
            pcm_data = PcmData(samples=samples, sample_rate=16000)
            
            # Mock the streaming client
            stt.streaming_client = Mock()
            stt.streaming_client.stream = Mock()
            
            with patch('getstream.plugins.assemblyai.stt.logger') as mock_logger:
                await stt._process_audio_impl(pcm_data)
                mock_logger.warning.assert_called()

    def test_event_emitter_inheritance(self, assemblyai_api_key):
        """Test that the plugin inherits from the correct base classes."""
        with patch('getstream.plugins.assemblyai.stt.stt._assemblyai_available', True), \
             patch('getstream.plugins.assemblyai.stt.stt.aai') as mock_aai, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClient') as mock_streaming_client, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClientOptions') as mock_options, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingEvents') as mock_events, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingParameters') as mock_params:
            mock_aai.settings.api_key = "test_key"
            mock_streaming_client.return_value = Mock()
            mock_options.return_value = Mock()
            mock_events.Begin = Mock()
            mock_events.Turn = Mock()
            mock_events.Termination = Mock()
            mock_events.Error = Mock()
            mock_params.return_value = Mock()
            from getstream.plugins.assemblyai import AssemblyAISTT
            stt = AssemblyAISTT(api_key=assemblyai_api_key)
            
            # Check that it has the expected methods
            assert hasattr(stt, 'on')
            assert hasattr(stt, 'emit')
            assert hasattr(stt, 'once')
            assert hasattr(stt, 'remove_listener')

    def test_provider_name_setting(self, assemblyai_api_key):
        """Test that the provider name is set correctly."""
        with patch('getstream.plugins.assemblyai.stt.stt._assemblyai_available', True), \
             patch('getstream.plugins.assemblyai.stt.stt.aai') as mock_aai, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClient') as mock_streaming_client, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClientOptions') as mock_options, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingEvents') as mock_events, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingParameters') as mock_params:
            mock_aai.settings.api_key = "test_key"
            mock_streaming_client.return_value = Mock()
            mock_options.return_value = Mock()
            mock_events.Begin = Mock()
            mock_events.Turn = Mock()
            mock_events.Termination = Mock()
            mock_events.Error = Mock()
            mock_params.return_value = Mock()
            from getstream.plugins.assemblyai import AssemblyAISTT
            stt = AssemblyAISTT(api_key=assemblyai_api_key)
            assert stt.provider_name == "assemblyai"


@pytest.mark.asyncio
class TestAssemblyAISTTAsync:
    """Async test cases for AssemblyAI STT plugin."""

    async def test_async_context_manager(self, assemblyai_api_key):
        """Test that the plugin can be used as an async context manager."""
        with patch('getstream.plugins.assemblyai.stt.stt._assemblyai_available', True), \
             patch('getstream.plugins.assemblyai.stt.stt.aai') as mock_aai, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClient') as mock_streaming_client, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClientOptions') as mock_options, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingEvents') as mock_events, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingParameters') as mock_params:
            mock_aai.settings.api_key = "test_key"
            mock_streaming_client.return_value = Mock()
            mock_options.return_value = Mock()
            mock_events.Begin = Mock()
            mock_events.Turn = Mock()
            mock_events.Termination = Mock()
            mock_events.Error = Mock()
            mock_params.return_value = Mock()
            from getstream.plugins.assemblyai import AssemblyAISTT
            async with AssemblyAISTT(api_key=assemblyai_api_key) as stt:
                assert stt is not None
                assert stt._is_closed is False
            
            # Should be closed after context manager
            assert stt._is_closed is True

    async def test_process_audio_connection_not_ready(self, assemblyai_api_key):
        """Test that audio processing fails when connection is not ready."""
        with patch('getstream.plugins.assemblyai.stt.stt._assemblyai_available', True), \
             patch('getstream.plugins.assemblyai.stt.stt.aai') as mock_aai, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClient') as mock_streaming_client, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingClientOptions') as mock_options, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingEvents') as mock_events, \
             patch('getstream.plugins.assemblyai.stt.stt.StreamingParameters') as mock_params:
            mock_aai.settings.api_key = "test_key"
            mock_streaming_client.return_value = Mock()
            mock_options.return_value = Mock()
            mock_events.Begin = Mock()
            mock_events.Turn = Mock()
            mock_events.Termination = Mock()
            mock_events.Error = Mock()
            mock_params.return_value = Mock()
            from getstream.plugins.assemblyai import AssemblyAISTT
            stt = AssemblyAISTT(api_key=assemblyai_api_key)
            
            # Create test PCM data
            samples = np.array([1000, -1000, 500, -500], dtype=np.int16)
            pcm_data = PcmData(samples=samples, sample_rate=48000)
            
            # Should raise exception when no connection
            with pytest.raises(Exception, match="No AssemblyAI connection available"):
                await stt._process_audio_impl(pcm_data)
