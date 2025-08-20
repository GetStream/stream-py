import pytest
import json
from datetime import datetime
from typing import Dict, Any

from getstream.plugins.common.events import (
    # Base events
    BaseEvent,
    EventType,
    ConnectionState,
    AudioFormat,
    create_event,
    
    # STT Events
    STTTranscriptEvent,
    STTPartialTranscriptEvent,
    STTErrorEvent,
    STTConnectionEvent,
    
    # TTS Events
    TTSAudioEvent,
    TTSSynthesisStartEvent,
    TTSSynthesisCompleteEvent,
    TTSErrorEvent,
    TTSConnectionEvent,
    
    # STS Events
    STSConnectedEvent,
    STSDisconnectedEvent,
    STSAudioInputEvent,
    STSAudioOutputEvent,
    STSTranscriptEvent,
    STSResponseEvent,
    STSConversationItemEvent,
    STSErrorEvent,
    
    # VAD Events
    VADSpeechStartEvent,
    VADSpeechEndEvent,
    VADAudioEvent,
    VADPartialEvent,
    VADErrorEvent,
    
    # Generic Events
    PluginInitializedEvent,
    PluginClosedEvent,
    PluginErrorEvent,
)

from getstream.plugins.common.event_serialization import (
    serialize_event,
    serialize_events,
    deserialize_event,
)


class TestBaseEvent:
    """Test the base event functionality."""
    
    def test_base_event_creation(self):
        """Test that base events can be created with minimal parameters."""
        event = BaseEvent(event_type=EventType.STT_TRANSCRIPT)
        assert event.event_id is not None
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)
        assert event.session_id is None
        assert event.user_metadata is None
        assert event.plugin_name is None
        assert event.plugin_version is None
    
    def test_base_event_with_optional_params(self):
        """Test base event creation with optional parameters."""
        session_id = "test-session-123"
        user_metadata = {"user_id": "user123"}
        plugin_name = "test_plugin"
        plugin_version = "1.0.0"
        
        event = BaseEvent(
            event_type=EventType.STT_TRANSCRIPT,
            session_id=session_id,
            user_metadata=user_metadata,
            plugin_name=plugin_name,
            plugin_version=plugin_version
        )
        
        assert event.session_id == session_id
        assert event.user_metadata == user_metadata
        assert event.plugin_name == plugin_name
        assert event.plugin_version == plugin_version


class TestSTTEvents:
    """Test STT-related events."""
    
    def test_stt_transcript_event_creation(self):
        """Test STT transcript event creation."""
        event = STTTranscriptEvent(text="Hello world")
        assert event.event_type == EventType.STT_TRANSCRIPT
        assert event.text == "Hello world"
        assert event.confidence is None  # Should be None by default
        assert event.language is None
        assert event.processing_time_ms is None
        assert event.audio_duration_ms is None
        assert event.model_name is None
        assert event.words is None
        assert event.is_final is True
    
    def test_stt_transcript_event_with_confidence(self):
        """Test STT transcript event with confidence."""
        event = STTTranscriptEvent(
            text="Hello world",
            confidence=0.95,
            language="en",
            processing_time_ms=100.0,
            audio_duration_ms=2000.0,
            model_name="test-model"
        )
        assert event.confidence == 0.95
        assert event.language == "en"
        assert event.processing_time_ms == 100.0
        assert event.audio_duration_ms == 2000.0
        assert event.model_name == "test-model"
    
    def test_stt_transcript_event_validation(self):
        """Test STT transcript event validation."""
        # Should raise ValueError for empty text
        with pytest.raises(ValueError, match="Transcript text cannot be empty"):
            STTTranscriptEvent(text="")
    
        # Whitespace-only text should pass validation (current behavior)
        event = STTTranscriptEvent(text="   ")
        assert event.text == "   "
        
        # Test that non-empty text works
        event = STTTranscriptEvent(text="Valid text")
        assert event.text == "Valid text"
    
    def test_stt_partial_transcript_event(self):
        """Test STT partial transcript event."""
        event = STTPartialTranscriptEvent(text="Hello")
        assert event.event_type == EventType.STT_PARTIAL_TRANSCRIPT
        assert event.text == "Hello"
        assert event.confidence is None
        assert event.is_final is False
    
    def test_stt_error_event(self):
        """Test STT error event."""
        error = Exception("Test error")
        event = STTErrorEvent(
            error=error,
            error_code="TEST_001",
            context="test context",
            retry_count=3,
            is_recoverable=False
        )
        assert event.event_type == EventType.STT_ERROR
        assert event.error == error
        assert event.error_code == "TEST_001"
        assert event.context == "test context"
        assert event.retry_count == 3
        assert event.is_recoverable is False
        assert event.error_message == "Test error"
    
    def test_stt_connection_event(self):
        """Test STT connection event."""
        event = STTConnectionEvent(
            connection_state=ConnectionState.CONNECTED,
            provider="test_provider",
            details={"test": "detail"},
            reconnect_attempts=2
        )
        assert event.event_type == EventType.STT_CONNECTION
        assert event.connection_state == ConnectionState.CONNECTED
        assert event.provider == "test_provider"
        assert event.details == {"test": "detail"}
        assert event.reconnect_attempts == 2


class TestTTSEvents:
    """Test TTS-related events."""
    
    def test_tts_audio_event_creation(self):
        """Test TTS audio event creation."""
        audio_data = b"test audio data"
        event = TTSAudioEvent(
            audio_data=audio_data,
            audio_format=AudioFormat.PCM_S16,
            sample_rate=22050,
            channels=2,
            chunk_index=5,
            is_final_chunk=False
        )
        assert event.event_type == EventType.TTS_AUDIO
        assert event.audio_data == audio_data
        assert event.audio_format == AudioFormat.PCM_S16
        assert event.sample_rate == 22050
        assert event.channels == 2
        assert event.chunk_index == 5
        assert event.is_final_chunk is False
    
    def test_tts_synthesis_start_event(self):
        """Test TTS synthesis start event."""
        event = TTSSynthesisStartEvent(
            text="Hello world",
            model_name="test-model",
            voice_id="voice123",
            estimated_duration_ms=5000.0
        )
        assert event.event_type == EventType.TTS_SYNTHESIS_START
        assert event.text == "Hello world"
        assert event.model_name == "test-model"
        assert event.voice_id == "voice123"
        assert event.estimated_duration_ms == 5000.0
        assert event.synthesis_id is not None
    
    def test_tts_synthesis_complete_event(self):
        """Test TTS synthesis complete event."""
        event = TTSSynthesisCompleteEvent(
            synthesis_id="synth123",
            text="Hello world",
            total_audio_bytes=1024,
            synthesis_time_ms=2500.0,
            audio_duration_ms=5000.0,
            chunk_count=10,
            real_time_factor=0.5
        )
        assert event.event_type == EventType.TTS_SYNTHESIS_COMPLETE
        assert event.synthesis_id == "synth123"
        assert event.text == "Hello world"
        assert event.total_audio_bytes == 1024
        assert event.synthesis_time_ms == 2500.0
        assert event.audio_duration_ms == 5000.0
        assert event.chunk_count == 10
        assert event.real_time_factor == 0.5
    
    def test_tts_error_event(self):
        """Test TTS error event."""
        error = Exception("TTS synthesis failed")
        event = TTSErrorEvent(
            error=error,
            error_code="TTS_001",
            context="synthesis",
            is_recoverable=True
        )
        assert event.event_type == EventType.TTS_ERROR
        assert event.error == error
        assert event.error_code == "TTS_001"
        assert event.context == "synthesis"
        assert event.is_recoverable is True
    
    def test_tts_connection_event(self):
        """Test TTS connection event."""
        event = TTSConnectionEvent(
            connection_state=ConnectionState.DISCONNECTED,
            provider="tts_provider",
            details={"reason": "timeout"}
        )
        assert event.event_type == EventType.TTS_CONNECTION
        assert event.connection_state == ConnectionState.DISCONNECTED
        assert event.provider == "tts_provider"
        assert event.details == {"reason": "timeout"}


class TestSTSEvents:
    """Test STS-related events."""
    
    def test_sts_connected_event(self):
        """Test STS connected event."""
        event = STSConnectedEvent(
            provider="sts_provider",
            session_config={"endpoint": "wss://test.com"}
        )
        assert event.event_type == EventType.STS_CONNECTED
        assert event.provider == "sts_provider"
        assert event.session_config == {"endpoint": "wss://test.com"}
    
    def test_sts_disconnected_event(self):
        """Test STS disconnected event."""
        event = STSDisconnectedEvent(
            provider="sts_provider",
            reason="user_disconnect",
            was_clean=True
        )
        assert event.event_type == EventType.STS_DISCONNECTED
        assert event.provider == "sts_provider"
        assert event.reason == "user_disconnect"
        assert event.was_clean is True
    
    def test_sts_audio_input_event(self):
        """Test STS audio input event."""
        event = STSAudioInputEvent(
            audio_data=b"input audio",
            sample_rate=16000,
            channels=1
        )
        assert event.event_type == EventType.STS_AUDIO_INPUT
        assert event.audio_data == b"input audio"
        assert event.sample_rate == 16000
        assert event.channels == 1
    
    def test_sts_audio_output_event(self):
        """Test STS audio output event."""
        event = STSAudioOutputEvent(
            audio_data=b"output audio",
            sample_rate=16000,
            channels=1
        )
        assert event.event_type == EventType.STS_AUDIO_OUTPUT
        assert event.audio_data == b"output audio"
        assert event.sample_rate == 16000
        assert event.channels == 1
    
    def test_sts_transcript_event(self):
        """Test STS transcript event."""
        event = STSTranscriptEvent(
            text="Hello world",
            confidence=0.95,
            is_user=True
        )
        assert event.event_type == EventType.STS_TRANSCRIPT
        assert event.text == "Hello world"
        assert event.confidence == 0.95
        assert event.is_user is True
    
    def test_sts_response_event(self):
        """Test STS response event."""
        event = STSResponseEvent(
            text="Response text",
            is_complete=True
        )
        assert event.event_type == EventType.STS_RESPONSE
        assert event.text == "Response text"
        assert event.is_complete is True
        assert event.response_id is not None
    
    def test_sts_conversation_item_event(self):
        """Test STS conversation item event."""
        event = STSConversationItemEvent(
            item_type="message",
            status="completed",
            role="user",
            content=[{"type": "text", "text": "User message"}]
        )
        assert event.event_type == EventType.STS_CONVERSATION_ITEM
        assert event.item_type == "message"
        assert event.status == "completed"
        assert event.role == "user"
        assert event.content == [{"type": "text", "text": "User message"}]
    
    def test_sts_error_event(self):
        """Test STS error event."""
        error = Exception("STS error")
        event = STSErrorEvent(
            error=error,
            error_code="STS_001",
            context="conversation"
        )
        assert event.event_type == EventType.STS_ERROR
        assert event.error == error
        assert event.error_code == "STS_001"
        assert event.context == "conversation"


class TestVADEvents:
    """Test VAD-related events."""
    
    def test_vad_speech_start_event(self):
        """Test VAD speech start event."""
        event = VADSpeechStartEvent(
            speech_probability=0.8,
            activation_threshold=0.5,
            frame_count=10
        )
        assert event.event_type == EventType.VAD_SPEECH_START
        assert event.speech_probability == 0.8
        assert event.activation_threshold == 0.5
        assert event.frame_count == 10
    
    def test_vad_speech_end_event(self):
        """Test VAD speech end event."""
        event = VADSpeechEndEvent(
            speech_probability=0.2,
            deactivation_threshold=0.3,
            total_speech_duration_ms=2500.0,
            total_frames=100
        )
        assert event.event_type == EventType.VAD_SPEECH_END
        assert event.speech_probability == 0.2
        assert event.deactivation_threshold == 0.3
        assert event.total_speech_duration_ms == 2500.0
        assert event.total_frames == 100
    
    def test_vad_audio_event(self):
        """Test VAD audio event."""
        event = VADAudioEvent(
            audio_data=b"speech audio",
            sample_rate=16000,
            audio_format="s16",
            channels=1,
            duration_ms=1000.0,
            speech_probability=0.9,
            frame_count=50
        )
        assert event.event_type == EventType.VAD_AUDIO
        assert event.audio_data == b"speech audio"
        assert event.sample_rate == 16000
        assert event.audio_format == "s16"
        assert event.channels == 1
        assert event.duration_ms == 1000.0
        assert event.speech_probability == 0.9
        assert event.frame_count == 50
    
    def test_vad_partial_event(self):
        """Test VAD partial event."""
        event = VADPartialEvent(
            speech_probability=0.7,
            frame_count=25,
            is_speech_active=True
        )
        assert event.event_type == EventType.VAD_PARTIAL
        assert event.speech_probability == 0.7
        assert event.frame_count == 25
        assert event.is_speech_active is True
    
    def test_vad_error_event(self):
        """Test VAD error event."""
        error = Exception("VAD processing error")
        event = VADErrorEvent(
            error=error,
            error_code="VAD_001",
            context="audio_processing",
            frame_data_available=False
        )
        assert event.event_type == EventType.VAD_ERROR
        assert event.error == error
        assert event.error_code == "VAD_001"
        assert event.context == "audio_processing"
        assert event.frame_data_available is False


class TestGenericEvents:
    """Test generic plugin events."""
    
    def test_plugin_initialized_event(self):
        """Test plugin initialized event."""
        event = PluginInitializedEvent(
            plugin_type="STT",
            provider="test_provider",
            configuration={"setting": "value"},
            capabilities=["transcription", "language_detection"]
        )
        assert event.event_type == EventType.PLUGIN_INITIALIZED
        assert event.plugin_type == "STT"
        assert event.provider == "test_provider"
        assert event.configuration == {"setting": "value"}
        assert event.capabilities == ["transcription", "language_detection"]
    
    def test_plugin_closed_event(self):
        """Test plugin closed event."""
        event = PluginClosedEvent(
            plugin_type="STT",
            provider="test_provider",
            reason="shutdown",
            cleanup_successful=True
        )
        assert event.event_type == EventType.PLUGIN_CLOSED
        assert event.plugin_type == "STT"
        assert event.provider == "test_provider"
        assert event.reason == "shutdown"
        assert event.cleanup_successful is True
    
    def test_plugin_error_event(self):
        """Test plugin error event."""
        error = Exception("Plugin error")
        event = PluginErrorEvent(
            plugin_type="STT",
            provider="test_provider",
            error=error,
            error_code="PLUGIN_001",
            context="initialization",
            is_fatal=False
        )
        assert event.event_type == EventType.PLUGIN_ERROR
        assert event.plugin_type == "STT"
        assert event.provider == "test_provider"
        assert event.error == error
        assert event.error_code == "PLUGIN_001"
        assert event.context == "initialization"
        assert event.is_fatal is False


class TestEventEnums:
    """Test event enums and constants."""
    
    def test_event_types(self):
        """Test that all event types are defined."""
        expected_types = [
            "stt_transcript",
            "stt_partial_transcript", 
            "stt_error",
            "stt_connection",
            "tts_audio",
            "tts_synthesis_start",
            "tts_synthesis_complete",
            "tts_error",
            "tts_connection",
            "sts_connected",
            "sts_disconnected",
            "sts_audio_input",
            "sts_audio_output",
            "sts_transcript",
            "sts_response",
            "sts_conversation_item",
            "sts_error",
            "vad_speech_start",
            "vad_speech_end",
            "vad_audio",
            "vad_partial",
            "vad_error",
            "plugin_initialized",
            "plugin_closed",
            "plugin_error"
        ]
        
        for expected_type in expected_types:
            assert hasattr(EventType, expected_type.upper().replace('-', '_')), f"Missing event type: {expected_type}"
    
    def test_connection_states(self):
        """Test connection state enum values."""
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.RECONNECTING.value == "reconnecting"
        assert ConnectionState.ERROR.value == "error"
    
    def test_audio_formats(self):
        """Test audio format enum values."""
        assert AudioFormat.PCM_S16.value == "s16"
        assert AudioFormat.PCM_F32.value == "f32"
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.OGG.value == "ogg"


class TestEventEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_event_with_none_values(self):
        """Test that events can handle None values gracefully."""
        event = STTTranscriptEvent(
            text="test",
            confidence=None,
            language=None,
            processing_time_ms=None
        )
        assert event.confidence is None
        assert event.language is None
        assert event.processing_time_ms is None
    
    def test_event_with_empty_strings(self):
        """Test that events can handle empty strings."""
        event = STTTranscriptEvent(
            text="test",
            language="",
            model_name=""
        )
        assert event.language == ""
        assert event.model_name == ""
    
    def test_event_with_zero_values(self):
        """Test that events can handle zero values."""
        event = STTTranscriptEvent(
            text="test",
            confidence=0.0,
            processing_time_ms=0.0,
            audio_duration_ms=0.0
        )
        assert event.confidence == 0.0
        assert event.processing_time_ms == 0.0
        assert event.audio_duration_ms == 0.0
    
    def test_event_serialization_compatibility(self):
        """Test that events can be converted to dict for serialization."""
        event = STTTranscriptEvent(
            text="test",
            confidence=0.95,
            language="en"
        )
        
        # Test that we can access all fields
        event_dict = {
            'text': event.text,
            'confidence': event.confidence,
            'language': event.language,
            'event_type': event.event_type.value,
            'event_id': event.event_id,
            'timestamp': event.timestamp.isoformat(),
            'is_final': event.is_final
        }
        
        assert event_dict['text'] == "test"
        assert event_dict['confidence'] == 0.95
        assert event_dict['language'] == "en"
        assert event_dict['event_type'] == "stt_transcript"
        assert event_dict['is_final'] is True


class TestEventSerialization:
    """Test event serialization and deserialization."""
    
    def test_serialize_stt_transcript_event(self):
        """Test serializing STT transcript event."""
        event = STTTranscriptEvent(
            text="Hello world",
            confidence=0.95,
            language="en",
            processing_time_ms=100.0,
            session_id="test-session",
            user_metadata={"user_id": "123"}
        )
        
        serialized = serialize_event(event)
        
        assert serialized['text'] == "Hello world"
        assert serialized['confidence'] == 0.95
        assert serialized['language'] == "en"
        assert serialized['processing_time_ms'] == 100.0
        assert serialized['session_id'] == "test-session"
        assert serialized['user_metadata'] == {"user_id": "123"}
        assert serialized['event_type'] == "stt_transcript"
        assert 'event_id' in serialized
        assert 'timestamp' in serialized
    
    def test_serialize_event_with_error(self):
        """Test serializing event with error field."""
        error = ValueError("Test error message")
        event = STTErrorEvent(
            error=error,
            error_code="TEST_001",
            context="test context"
        )
        
        serialized = serialize_event(event)
        
        assert serialized['error']['type'] == "ValueError"
        assert serialized['error']['message'] == "Test error message"
        assert serialized['error_code'] == "TEST_001"
        assert serialized['context'] == "test context"
        assert serialized['event_type'] == "stt_error"
    
    def test_serialize_event_with_audio_data(self):
        """Test serializing event with audio data."""
        audio_data = b"fake audio data" * 100  # Create some dummy audio data
        event = TTSAudioEvent(
            audio_data=audio_data,
            sample_rate=22050,
            channels=2
        )
        
        serialized = serialize_event(event)
        
        # Audio data should be replaced with metadata
        assert serialized['audio_data']['size_bytes'] == len(audio_data)
        assert serialized['audio_data']['type'] == 'bytes'
        assert serialized['sample_rate'] == 22050
        assert serialized['channels'] == 2
        assert serialized['event_type'] == "tts_audio"
    
    def test_serialize_events_list(self):
        """Test serializing a list of events to JSON."""
        events = [
            STTTranscriptEvent(text="First transcript"),
            STTPartialTranscriptEvent(text="Partial"),
            STTErrorEvent(error=Exception("Test error"))
        ]
        
        json_string = serialize_events(events)
        
        # Should be valid JSON
        parsed = json.loads(json_string)
        assert len(parsed) == 3
        assert parsed[0]['text'] == "First transcript"
        assert parsed[0]['event_type'] == "stt_transcript"
        assert parsed[1]['text'] == "Partial"
        assert parsed[1]['event_type'] == "stt_partial_transcript"
        assert parsed[2]['event_type'] == "stt_error"
    
    def test_deserialize_stt_transcript_event(self):
        """Test deserializing STT transcript event."""
        original_event = STTTranscriptEvent(
            text="Hello world",
            confidence=0.95,
            language="en",
            processing_time_ms=100.0
        )
        
        # Serialize and then deserialize
        serialized = serialize_event(original_event)
        deserialized = deserialize_event(serialized)
        
        assert isinstance(deserialized, STTTranscriptEvent)
        assert deserialized.text == "Hello world"
        assert deserialized.confidence == 0.95
        assert deserialized.language == "en"
        assert deserialized.processing_time_ms == 100.0
        assert deserialized.event_type == EventType.STT_TRANSCRIPT
    
    def test_deserialize_event_with_error(self):
        """Test deserializing event with error field."""
        original_event = STTErrorEvent(
            error=ValueError("Original error"),
            error_code="TEST_001",
            context="test context"
        )
        
        serialized = serialize_event(original_event)
        deserialized = deserialize_event(serialized)
        
        assert isinstance(deserialized, STTErrorEvent)
        assert isinstance(deserialized.error, Exception)
        assert str(deserialized.error) == "Original error"
        assert deserialized.error_code == "TEST_001"
        assert deserialized.context == "test context"
    
    def test_deserialize_event_with_audio_data_placeholder(self):
        """Test deserializing event with audio data placeholder."""
        original_event = TTSAudioEvent(
            audio_data=b"test audio",
            sample_rate=16000,
            channels=1
        )
        
        serialized = serialize_event(original_event)
        deserialized = deserialize_event(serialized)
        
        assert isinstance(deserialized, TTSAudioEvent)
        assert deserialized.audio_data is None  # Audio data should be removed
        assert deserialized.sample_rate == 16000
        assert deserialized.channels == 1
    
    def test_deserialize_event_with_timestamp_string(self):
        """Test deserializing event with string timestamp."""
        data = {
            'event_type': 'stt_transcript',
            'text': 'Test text',
            'timestamp': '2023-12-01T10:30:00',
            'event_id': 'test-id-123'
        }
        
        deserialized = deserialize_event(data)
        
        assert isinstance(deserialized, STTTranscriptEvent)
        assert deserialized.text == 'Test text'
        assert isinstance(deserialized.timestamp, datetime)
        assert deserialized.timestamp.year == 2023
        assert deserialized.timestamp.month == 12
    
    def test_deserialize_invalid_event_type(self):
        """Test deserializing with invalid event type."""
        data = {
            'event_type': 'invalid_event_type',
            'text': 'Test text'
        }
        
        with pytest.raises(ValueError, match="Unknown event type: invalid_event_type"):
            deserialize_event(data)
    
    def test_deserialize_missing_event_type(self):
        """Test deserializing with missing event type."""
        data = {
            'text': 'Test text'
        }
        
        with pytest.raises(ValueError, match="Event data missing event_type"):
            deserialize_event(data)
    
    def test_round_trip_serialization_all_event_types(self):
        """Test round-trip serialization for all major event types."""
        test_events = [
            # STT Events
            STTTranscriptEvent(text="Test transcript", confidence=0.9),
            STTPartialTranscriptEvent(text="Partial text"),
            STTErrorEvent(error=Exception("STT error")),
            STTConnectionEvent(connection_state=ConnectionState.CONNECTED),
            
            # TTS Events  
            TTSAudioEvent(audio_data=b"audio", sample_rate=16000),
            TTSSynthesisStartEvent(text="Synthesis text"),
            TTSSynthesisCompleteEvent(synthesis_id="synth-123"),
            TTSErrorEvent(error=Exception("TTS error")),
            TTSConnectionEvent(connection_state=ConnectionState.DISCONNECTED),
            
            # STS Events
            STSConnectedEvent(provider="test_provider"),
            STSDisconnectedEvent(reason="user_disconnect"),
            STSAudioInputEvent(audio_data=b"input"),
            STSAudioOutputEvent(audio_data=b"output"),
            STSTranscriptEvent(text="STS transcript"),
            STSResponseEvent(text="STS response"),
            STSConversationItemEvent(item_type="message"),
            STSErrorEvent(error=Exception("STS error")),
            
            # VAD Events
            VADSpeechStartEvent(speech_probability=0.8),
            VADSpeechEndEvent(total_speech_duration_ms=1000.0),
            VADAudioEvent(audio_data=b"vad audio"),
            VADPartialEvent(speech_probability=0.7),
            VADErrorEvent(error=Exception("VAD error")),
            
            # Generic Events
            PluginInitializedEvent(plugin_type="STT"),
            PluginClosedEvent(plugin_type="TTS"),
            PluginErrorEvent(plugin_type="VAD", error=Exception("Plugin error"))
        ]
        
        for original_event in test_events:
            # Serialize
            serialized = serialize_event(original_event)
            
            # Deserialize
            deserialized = deserialize_event(serialized)
            
            # Verify type and basic properties
            assert type(deserialized) == type(original_event)
            assert deserialized.event_type == original_event.event_type
            
            # Verify specific properties based on event type
            if hasattr(original_event, 'text') and original_event.text:
                assert deserialized.text == original_event.text
            
            if hasattr(original_event, 'error') and original_event.error:
                assert isinstance(deserialized.error, Exception)
                assert str(deserialized.error) == str(original_event.error)
    
    def test_create_event_function(self):
        """Test the create_event factory function."""
        # Test creating different event types
        stt_event = create_event(EventType.STT_TRANSCRIPT, text="Test text")
        assert isinstance(stt_event, STTTranscriptEvent)
        assert stt_event.text == "Test text"
        
        tts_event = create_event(EventType.TTS_AUDIO, sample_rate=22050)
        assert isinstance(tts_event, TTSAudioEvent)
        assert tts_event.sample_rate == 22050
        
        vad_event = create_event(EventType.VAD_SPEECH_START, speech_probability=0.9)
        assert isinstance(vad_event, VADSpeechStartEvent)
        assert vad_event.speech_probability == 0.9
    
    def test_create_event_invalid_type(self):
        """Test create_event with invalid event type."""
        # Test with None (which should raise an error)
        with pytest.raises((ValueError, TypeError)):
            create_event(None, text="test")
    
    def test_json_round_trip_serialization(self):
        """Test complete JSON round-trip serialization."""
        events = [
            STTTranscriptEvent(text="First", confidence=0.95),
            STTErrorEvent(error=ValueError("Test error"), error_code="E001"),
            TTSAudioEvent(audio_data=b"audio data", sample_rate=16000)
        ]
        
        # Serialize to JSON string
        json_string = serialize_events(events)
        
        # Parse JSON and deserialize each event
        events_data = json.loads(json_string)
        deserialized_events = [deserialize_event(event_data) for event_data in events_data]
        
        # Verify we got the same number and types of events
        assert len(deserialized_events) == 3
        assert isinstance(deserialized_events[0], STTTranscriptEvent)
        assert isinstance(deserialized_events[1], STTErrorEvent)
        assert isinstance(deserialized_events[2], TTSAudioEvent)
        
        # Verify content
        assert deserialized_events[0].text == "First"
        assert deserialized_events[0].confidence == 0.95
        assert str(deserialized_events[1].error) == "Test error"
        assert deserialized_events[1].error_code == "E001"
        assert deserialized_events[2].sample_rate == 16000
        assert deserialized_events[2].audio_data is None  # Should be removed during serialization
