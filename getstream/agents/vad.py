import abc
import logging
from typing import List, Optional, Dict, Any

import numpy as np
from pyee.asyncio import AsyncIOEventEmitter

from getstream.video.rtc.track_util import PcmData

logger = logging.getLogger(__name__)

class VAD(AsyncIOEventEmitter, abc.ABC):
    """
    Voice Activity Detection base class. 
    
    This abstract class provides the interface for voice activity detection
    implementations. It handles:
    - Receiving audio data as PCM
    - Detecting speech vs. silence
    - Accumulating speech and discarding silence
    - Flushing accumulated speech when a pause is detected
    - Emitting "audio" events with the speech data
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_size: int = 512,
        silence_threshold: float = 0.5,
        speech_pad_ms: int = 300,
        min_speech_ms: int = 250,
        max_speech_ms: int = 30000,
    ):
        """
        Initialize the VAD.
        
        Args:
            sample_rate: Audio sample rate in Hz
            frame_size: Size of audio frames to process
            silence_threshold: Threshold for detecting silence (0.0 to 1.0)
            speech_pad_ms: Number of milliseconds to pad before/after speech
            min_speech_ms: Minimum milliseconds of speech to emit
            max_speech_ms: Maximum milliseconds of speech before forced flush
        """
        super().__init__()
        
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self.silence_threshold = silence_threshold
        self.speech_pad_frames = int(speech_pad_ms * sample_rate / 1000 / frame_size)
        self.min_speech_frames = int(min_speech_ms * sample_rate / 1000 / frame_size)
        self.max_speech_frames = int(max_speech_ms * sample_rate / 1000 / frame_size)
        
        # State variables
        self.speech_buffer: List[np.ndarray] = []
        self.silence_counter = 0
        self.is_speech_active = False
        self.total_speech_frames = 0
        
    @abc.abstractmethod
    async def is_speech(self, frame: PcmData) -> float:
        """
        Determine if the audio frame contains speech.
        
        Args:
            frame: Audio frame data as PcmData
            
        Returns:
            Probability (0.0 to 1.0) that the frame contains speech
        """
        pass
    
    async def process_audio(self, pcm_data: PcmData, user: Optional[Dict[str, Any]] = None) -> None:
        """
        Process raw PCM audio data for voice activity detection.
        
        Args:
            pcm_data: Raw PCM audio data
            user: User metadata to include with emitted audio events
        """

        if pcm_data.sample_rate != self.sample_rate:
            raise TypeError(f"vad is initialized with sample rate {self.sample_rate} but pcm data has sample rate {pcm_data.sample_rate}")

        # Process audio in frames
        for i in range(0, len(pcm_data.samples), self.frame_size):
            if i + self.frame_size > len(pcm_data.samples):
                # Not enough samples for a full frame, pad with zeros
                # TODO: this might not be ideal (to pad with zeroes)
                frame = np.zeros(self.frame_size, dtype=np.int16)
                frame[:len(pcm_data.samples) - i] = pcm_data.samples[i:]
            else:
                frame = pcm_data.samples[i:i+self.frame_size]
            
            await self._process_frame(PcmData(samples=frame, sample_rate=pcm_data.sample_rate, format=pcm_data.format), user)
    
    async def _process_frame(self, frame: PcmData, user: Optional[Dict[str, Any]] = None) -> None:
        """
        Process a single audio frame.
        
        Args:
            frame: Audio frame as numpy array
            user: User metadata to include with emitted audio events
        """
        speech_prob = await self.is_speech(frame)
        is_speech = speech_prob > self.silence_threshold
        
        # Add frame to buffer in all cases during active speech
        if self.is_speech_active:
            self.speech_buffer.append(frame.samples)
            self.total_speech_frames += 1
            
            if is_speech:
                # Reset silence counter when speech is detected
                self.silence_counter = 0
            else:
                # Increment silence counter when silence is detected
                self.silence_counter += 1
                
                # If silence exceeds padding duration, emit audio and reset
                if self.silence_counter >= self.speech_pad_frames:
                    await self._flush_speech_buffer(user)
                    
            # Force flush if speech duration exceeds maximum
            if self.total_speech_frames >= self.max_speech_frames:
                await self._flush_speech_buffer(user)
        
        # Start collecting speech when detected
        elif is_speech:
            self.is_speech_active = True
            self.silence_counter = 0
            self.total_speech_frames = 0
            
            # Add this frame to the buffer
            self.speech_buffer.append(frame.samples)
            self.total_speech_frames += 1
    
    async def _flush_speech_buffer(self, user: Optional[Dict[str, Any]] = None) -> None:
        """
        Flush the accumulated speech buffer if it meets minimum length requirements.
        
        Args:
            user: User metadata to include with emitted audio events
        """
        if len(self.speech_buffer) >= self.min_speech_frames:
            # Concatenate all frames in the buffer
            speech_data = np.concatenate(self.speech_buffer)
            
            # Emit the audio event
            self.emit("audio", PcmData(sample_rate=self.sample_rate, samples=speech_data, format="s16"), user)
            logger.debug(f"Emitted audio event with {len(speech_data)} samples")
        
        # Reset state variables
        self.speech_buffer = []
        self.silence_counter = 0
        self.is_speech_active = False
        self.total_speech_frames = 0
    
    async def reset(self) -> None:
        """Reset the VAD state."""
        self.speech_buffer = []
        self.silence_counter = 0
        self.is_speech_active = False
        self.total_speech_frames = 0