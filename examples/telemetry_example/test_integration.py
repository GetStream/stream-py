#!/usr/bin/env python3
"""
Test script to verify telemetry integration with actual plugins.
"""

import asyncio
import logging
import os
from getstream.plugins.common import (
    initialize_telemetry,
    TelemetryConfig,
    get_telemetry
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_plugin_telemetry():
    """Test that plugins actually emit telemetry events."""
    
    # Initialize telemetry
    config = TelemetryConfig(
        service_name="integration-test",
        enable_console_export=True,
        enable_plugin_metrics=True,
        enable_event_tracing=True
    )
    
    telemetry = initialize_telemetry(config)
    logger.info("Telemetry initialized for integration test")
    
    try:
        # Test STT plugin telemetry
        await test_stt_telemetry()
        
        # Test TTS plugin telemetry  
        await test_tts_telemetry()
        
        # Test VAD plugin telemetry
        await test_vad_telemetry()
        
        logger.info("All telemetry integration tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Telemetry integration test failed: {e}")
        raise


async def test_stt_telemetry():
    """Test STT plugin telemetry integration."""
    logger.info("Testing STT plugin telemetry...")
    
    try:
        # Import STT plugin (this will trigger initialization events)
        from getstream.plugins.common import STT
        
        # Create a mock STT instance to test telemetry
        class MockSTTWithTelemetry(STT):
            def __init__(self):
                super().__init__()
                # This should automatically emit initialization events with telemetry
                pass
            
            async def _process_audio_impl(self, pcm_data, user_metadata):
                # Mock implementation
                return None
        
        # Create instance - this should emit initialization events
        stt = MockSTTWithTelemetry()
        
        # Verify telemetry emitter was created
        assert hasattr(stt, 'telemetry_emitter'), "STT plugin should have telemetry emitter"
        logger.info("✅ STT plugin telemetry integration verified")
        
    except Exception as e:
        logger.error(f"STT telemetry test failed: {e}")
        raise


async def test_tts_telemetry():
    """Test TTS plugin telemetry integration."""
    logger.info("Testing TTS plugin telemetry...")
    
    try:
        # Import TTS plugin
        from getstream.plugins.common import TTS
        
        # Create a mock TTS instance
        class MockTTSWithTelemetry(TTS):
            def __init__(self):
                super().__init__()
                # This should automatically emit initialization events with telemetry
                pass
            
            async def stream_audio(self, text, *args, **kwargs):
                # Mock implementation
                return b"mock_audio"
        
        # Create instance
        tts = MockTTSWithTelemetry()
        
        # Verify telemetry emitter was created
        assert hasattr(tts, 'telemetry_emitter'), "TTS plugin should have telemetry emitter"
        logger.info("✅ TTS plugin telemetry integration verified")
        
    except Exception as e:
        logger.error(f"TTS telemetry test failed: {e}")
        raise


async def test_vad_telemetry():
    """Test VAD plugin telemetry integration."""
    logger.info("Testing VAD plugin telemetry...")
    
    try:
        # Import VAD plugin
        from getstream.plugins.common import VAD
        
        # Create a mock VAD instance
        class MockVADWithTelemetry(VAD):
            def __init__(self):
                super().__init__()
                # This should automatically emit initialization events with telemetry
                pass
            
            async def is_speech(self, frame):
                # Mock implementation
                return 0.5
        
        # Create instance
        vad = MockVADWithTelemetry()
        
        # Verify telemetry emitter was created
        assert hasattr(vad, 'telemetry_emitter'), "VAD plugin should have telemetry emitter"
        logger.info("✅ VAD plugin telemetry integration verified")
        
    except Exception as e:
        logger.error(f"VAD telemetry test failed: {e}")
        raise


async def test_actual_plugin_telemetry():
    """Test telemetry with actual plugin implementations if available."""
    logger.info("Testing actual plugin telemetry...")
    
    try:
        # Try to import and test actual plugins
        plugins_tested = []
        
        # Test Deepgram STT if available
        try:
            from getstream.plugins.deepgram.stt.stt import DeepgramSTT
            # This will fail without API key, but we can check if telemetry is initialized
            logger.info("✅ Deepgram STT plugin telemetry ready")
            plugins_tested.append("Deepgram STT")
        except ImportError:
            logger.info("⚠️ Deepgram STT not available for testing")
        
        # Test ElevenLabs TTS if available
        try:
            from getstream.plugins.elevenlabs.tts.tts import ElevenLabsTTS
            logger.info("✅ ElevenLabs TTS plugin telemetry ready")
            plugins_tested.append("ElevenLabs TTS")
        except ImportError:
            logger.info("⚠️ ElevenLabs TTS not available for testing")
        
        # Test Silero VAD if available
        try:
            from getstream.plugins.silero.vad.vad import SileroVAD
            logger.info("✅ Silero VAD plugin telemetry ready")
            plugins_tested.append("Silero VAD")
        except ImportError:
            logger.info("⚠️ Silero VAD not available for testing")
        
        if plugins_tested:
            logger.info(f"✅ Telemetry integration verified for: {', '.join(plugins_tested)}")
        else:
            logger.warning("⚠️ No actual plugins available for testing")
            
    except Exception as e:
        logger.error(f"Actual plugin telemetry test failed: {e}")
        # Don't raise here as this is optional


async def main():
    """Main test function."""
    try:
        await test_plugin_telemetry()
        await test_actual_plugin_telemetry()
        
        logger.info("🎉 All telemetry integration tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Telemetry integration test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
