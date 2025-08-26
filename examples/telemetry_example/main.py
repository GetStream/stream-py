#!/usr/bin/env python3
"""
OpenTelemetry Integration Example for GetStream AI Plugins.

This example demonstrates how to use the OpenTelemetry integration
for comprehensive observability of plugin operations.
"""

import asyncio
import logging
import os
import time
from typing import Optional

# Import the telemetry components
from getstream.plugins.common import (
    # Core telemetry
    initialize_telemetry,
    get_telemetry,
    TelemetryConfig,
    PluginTelemetry,
    trace_plugin_operation,
    
    # Telemetry event system
    TelemetryEventEmitter,
    TelemetryEventFilter,
    
    # Telemetry registry
    TelemetryEventRegistry,
    get_global_telemetry_registry,
    
    # Event system
    EventType,
    create_event,
    STTTranscriptEvent,
    TTSAudioEvent,
    PluginErrorEvent,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockSTTPlugin:
    """Mock STT plugin demonstrating telemetry integration."""
    
    def __init__(self, plugin_name: str = "mock_stt"):
        self.plugin_name = plugin_name
        
        # Initialize telemetry
        self.telemetry = get_telemetry()
        
        # Create telemetry event emitter
        self.event_emitter = TelemetryEventEmitter(plugin_name)
        
        # Create telemetry event registry
        self.event_registry = TelemetryEventRegistry(
            max_events=1000,
            telemetry=self.telemetry
        )
    
    @trace_plugin_operation("transcribe_audio", "mock_stt")
    async def transcribe_audio(self, audio_data: bytes, session_id: str) -> str:
        """Transcribe audio with telemetry integration."""
        
        # Start operation timing
        self.event_emitter.start_operation("transcribe_audio", {
            "audio_size_bytes": len(audio_data),
            "session_id": session_id
        })
        
        try:
            # Simulate processing time
            await asyncio.sleep(0.1)
            
            # Create transcript event
            transcript_event = create_event(
                EventType.STT_TRANSCRIPT,
                text="Hello, this is a test transcript",
                confidence=0.95,
                processing_time_ms=100.0,
                plugin_name=self.plugin_name,
                session_id=session_id,
                model_name="mock_model_v1"
            )
            
            # Emit event with telemetry
            self.event_emitter.emit_with_trace(
                transcript_event,
                "transcribe_audio",
                {"audio_size_bytes": len(audio_data)}
            )
            
            # Register event in registry
            self.event_registry.register_event(transcript_event)
            
            # End operation successfully
            self.event_emitter.end_operation(
                "transcribe_audio",
                success=True,
                event=transcript_event
            )
            
            return transcript_event.text
            
        except Exception as e:
            # End operation with failure
            self.event_emitter.end_operation(
                "transcribe_audio",
                success=False
            )
            
            # Emit error event
            self.event_emitter.emit_error(
                e,
                EventType.STT_ERROR,
                {"audio_size_bytes": len(audio_data)},
                session_id
            )
            
            raise
    
    async def batch_transcribe(self, audio_files: list, session_id: str):
        """Demonstrate batch processing with telemetry."""
        
        with self.event_emitter.operation_context(
            "batch_transcribe",
            {"file_count": len(audio_files), "session_id": session_id}
        ):
            results = []
            
            for i, audio_file in enumerate(audio_files):
                try:
                    # Simulate processing each file
                    await asyncio.sleep(0.05)
                    
                    # Create partial transcript event
                    partial_event = create_event(
                        EventType.STT_PARTIAL_TRANSCRIPT,
                        text=f"Partial result {i+1}",
                        confidence=0.8,
                        processing_time_ms=50.0,
                        plugin_name=self.plugin_name,
                        session_id=session_id,
                        is_final=False
                    )
                    
                    # Emit partial event
                    self.event_emitter.emit(partial_event)
                    self.event_registry.register_event(partial_event)
                    
                    results.append(partial_event.text)
                    
                except Exception as e:
                    logger.error(f"Error processing file {i}: {e}")
                    self.telemetry.record_error(e, {
                        "file_index": i,
                        "operation": "batch_transcribe"
                    })
            
            return results


class MockTTSPlugin:
    """Mock TTS plugin demonstrating telemetry integration."""
    
    def __init__(self, plugin_name: str = "mock_tts"):
        self.plugin_name = plugin_name
        self.telemetry = get_telemetry()
        self.event_emitter = TelemetryEventEmitter(plugin_name)
    
    async def synthesize_speech(self, text: str, session_id: str) -> bytes:
        """Synthesize speech with telemetry integration."""
        
        with self.event_emitter.operation_context(
            "synthesize_speech",
            {"text_length": len(text), "session_id": session_id}
        ):
            # Simulate synthesis time
            await asyncio.sleep(0.2)
            
            # Create synthesis start event
            start_event = create_event(
                EventType.TTS_SYNTHESIS_START,
                text=text,
                plugin_name=self.plugin_name,
                session_id=session_id,
                model_name="mock_tts_model"
            )
            
            self.event_emitter.emit(start_event)
            
            # Simulate audio generation
            audio_data = b"mock_audio_data" * 100
            
            # Create audio event
            audio_event = create_event(
                EventType.TTS_AUDIO,
                audio_data=audio_data,
                plugin_name=self.plugin_name,
                session_id=session_id,
                chunk_index=0,
                is_final_chunk=True
            )
            
            self.event_emitter.emit(audio_event)
            
            # Create completion event
            completion_event = create_event(
                EventType.TTS_SYNTHESIS_COMPLETE,
                synthesis_id=start_event.synthesis_id,
                text=text,
                total_audio_bytes=len(audio_data),
                synthesis_time_ms=200.0,
                audio_duration_ms=1000.0,
                chunk_count=1,
                real_time_factor=0.5,
                plugin_name=self.plugin_name,
                session_id=session_id
            )
            
            self.event_emitter.emit(completion_event)
            
            return audio_data


async def demonstrate_telemetry():
    """Demonstrate the telemetry integration."""
    
    # Initialize telemetry with custom configuration
    config = TelemetryConfig(
        service_name="telemetry-example",
        service_version="1.0.0",
        enable_console_export=True,
        enable_plugin_metrics=True,
        enable_event_tracing=True,
        enable_performance_metrics=True
    )
    
    telemetry = initialize_telemetry(config)
    logger.info("Telemetry initialized")
    
    # Create plugins
    stt_plugin = MockSTTPlugin()
    tts_plugin = MockTTSPlugin()
    
    # Get global telemetry registry
    global_registry = get_global_telemetry_registry()
    
    # Demonstrate STT operations
    logger.info("Demonstrating STT operations...")
    
    session_id = "session_123"
    
    # Single transcription
    transcript = await stt_plugin.transcribe_audio(b"mock_audio", session_id)
    logger.info(f"Transcript: {transcript}")
    
    # Batch transcription
    audio_files = [b"audio1", b"audio2", b"audio3"]
    batch_results = await stt_plugin.batch_transcribe(audio_files, session_id)
    logger.info(f"Batch results: {batch_results}")
    
    # Demonstrate TTS operations
    logger.info("Demonstrating TTS operations...")
    
    audio_output = await tts_plugin.synthesize_speech(
        "Hello, this is a test synthesis",
        session_id
    )
    logger.info(f"Generated audio: {len(audio_output)} bytes")
    
    # Wait a bit for metrics to be exported
    await asyncio.sleep(1)
    
    # Get telemetry statistics
    logger.info("Getting telemetry statistics...")
    
    # Registry statistics
    registry_stats = global_registry.get_statistics()
    logger.info(f"Registry stats: {registry_stats}")
    
    # Plugin-specific statistics
    stt_stats = stt_plugin.event_registry.get_statistics()
    logger.info(f"STT plugin stats: {stt_stats}")
    
    # Error summary
    error_summary = global_registry.get_error_summary()
    logger.info(f"Error summary: {error_summary}")
    
    # Performance summary
    performance_summary = global_registry.get_performance_summary()
    logger.info(f"Performance summary: {performance_summary}")
    
    # Get telemetry summary from event emitters
    stt_summary = stt_plugin.event_emitter.get_telemetry_summary()
    logger.info(f"STT emitter summary: {stt_summary}")
    
    # Demonstrate error handling
    logger.info("Demonstrating error handling...")
    
    try:
        await stt_plugin.transcribe_audio(b"", session_id)
    except Exception as e:
        logger.info(f"Expected error caught: {e}")
    
    # Wait for final metrics export
    await asyncio.sleep(1)
    
    logger.info("Telemetry demonstration completed!")


async def demonstrate_environment_configuration():
    """Demonstrate environment-based configuration."""
    
    logger.info("Demonstrating environment-based configuration...")
    
    # Set environment variables for telemetry
    os.environ["OTEL_SERVICE_NAME"] = "env-configured-service"
    os.environ["OTEL_SERVICE_VERSION"] = "2.0.0"
    os.environ["OTEL_TRACES_ENABLED"] = "true"
    os.environ["OTEL_METRICS_ENABLED"] = "true"
    os.environ["OTEL_LOGS_ENABLED"] = "true"
    os.environ["OTEL_CONSOLE_EXPORT"] = "true"
    
    # Initialize telemetry from environment
    telemetry = initialize_telemetry()
    logger.info(f"Telemetry initialized with config: {telemetry.config}")
    
    # Create a simple plugin
    plugin = MockSTTPlugin("env_stt")
    
    # Perform some operations
    transcript = await plugin.transcribe_audio(b"test_audio", "env_session")
    logger.info(f"Environment-configured plugin transcript: {transcript}")
    
    # Wait for metrics export
    await asyncio.sleep(1)
    
    logger.info("Environment configuration demonstration completed!")


async def main():
    """Main function to run the telemetry demonstration."""
    
    try:
        # Run the main telemetry demonstration
        await demonstrate_telemetry()
        
        # Run environment configuration demonstration
        await demonstrate_environment_configuration()
        
    except Exception as e:
        logger.error(f"Error in telemetry demonstration: {e}")
        raise
    
    finally:
        # Shutdown telemetry gracefully
        logger.info("Shutting down telemetry...")
        shutdown_telemetry()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
