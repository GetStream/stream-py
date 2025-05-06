import logging
import torch
import numpy as np

from getstream.agents.vad import VAD
from getstream.video.rtc.track_util import PcmData

logger = logging.getLogger(__name__)


class Silero(VAD):
    """
    Voice Activity Detection implementation using Silero VAD model.

    This class implements the VAD interface using the Silero VAD model,
    which is a high-performance speech detection model.
    """

    def __init__(
        self,
        sample_rate: int = 48000,
        frame_size: int = 512,
        silence_threshold: float = 0.2,
        speech_pad_ms: int = 300,
        min_speech_ms: int = 250,
        max_speech_ms: int = 30000,
    ):
        """
        Initialize the Silero VAD.

        Args:
            sample_rate: Audio sample rate in Hz expected
            frame_size: Size of audio frames to process
            silence_threshold: Threshold for detecting silence (0.0 to 1.0)
            speech_pad_ms: Number of milliseconds to pad before/after speech
            min_speech_ms: Minimum milliseconds of speech to emit
            max_speech_ms: Maximum milliseconds of speech before forced flush
        """
        super().__init__(
            sample_rate=sample_rate,
            frame_size=frame_size,
            silence_threshold=silence_threshold,
            speech_pad_ms=speech_pad_ms,
            min_speech_ms=min_speech_ms,
            max_speech_ms=max_speech_ms,
        )

        # Buffer for accumulating audio frames for Silero model
        self.audio_buffer = []

        # Minimum milliseconds of audio needed for Silero to work properly
        self.min_silero_audio_ms = 30

        # Calculate buffer size based on sample rate
        self.min_buffer_samples = int(self.min_silero_audio_ms * sample_rate / 1000)

        self._load_model()

    def _load_model(self) -> None:
        """Load the Silero VAD model using torch hub."""
        try:
            logger.info("Loading Silero VAD model from torch hub")

            # Use torch.hub to load the model and utils
            self.model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                trust_repo=True,
            )

            # Set model to evaluation mode
            self.model.eval()

            # Set the device (CPU in this case)
            self.device = torch.device("cpu")
            self.model.to(self.device)

            # Initialize necessary for prediction
            self.reset_states()

            logger.info("Silero VAD model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            raise

    def reset_states(self) -> None:
        """Reset the model states."""
        # Clear audio buffer only - no longer need to maintain h and c states
        self.audio_buffer = []

    def _resample_audio(
        self, frame: np.ndarray, from_rate: int, to_rate: int
    ) -> np.ndarray:
        """
        Resample audio from one sample rate to another using simple averaging.

        Args:
            frame: Audio frame as numpy array
            from_rate: Original sample rate
            to_rate: Target sample rate

        Returns:
            Resampled audio frame
        """
        if from_rate == to_rate:
            return frame

        # Calculate the ratio for resampling
        ratio = from_rate // to_rate

        if from_rate % to_rate != 0:
            logger.warning(
                f"Resampling from {from_rate} to {to_rate} Hz is not an integer ratio"
            )

        # Reshape the frame to handle the exact number of samples
        # Trim if necessary to make it divisible by ratio
        trim_size = len(frame) - (len(frame) % ratio)
        if trim_size < len(frame):
            frame = frame[:trim_size]

        # Reshape and average
        resampled = frame.reshape(-1, ratio).mean(axis=1)

        logger.debug(
            f"Resampled audio from {len(frame)} samples to {len(resampled)} samples"
        )
        return resampled

    async def is_speech(self, frame: PcmData) -> float:
        """
        Detect speech in an audio frame using the Silero VAD model.

        Args:
            frame: PcmData object containing audio samples

        Returns:
            Probability (0.0 to 1.0) that the frame contains speech
        """
        try:
            # Convert PCM data to float32 in range [-1.0, 1.0]
            audio_array = frame.samples.astype(np.float32) / 32768.0

            # Add current frame to buffer
            self.audio_buffer.append(audio_array)

            # Calculate total samples in buffer
            buffer_samples = sum(len(f) for f in self.audio_buffer)

            # If we have fewer samples than required, return a low probability
            # This avoids processing with Silero until we have enough audio data
            if buffer_samples < self.min_buffer_samples:
                return 0.0

            # Concatenate all frames in the buffer
            concatenated_frame = np.concatenate(self.audio_buffer)

            # Reset buffer for next time
            self.audio_buffer = []

            # Resample the audio if needed (e.g., from 48000 Hz to 16000 Hz)
            model_sample_rate = 16000  # The model works with 16kHz audio
            if frame.sample_rate != model_sample_rate:
                concatenated_frame = self._resample_audio(
                    concatenated_frame, frame.sample_rate, model_sample_rate
                )

            # The Silero VAD model requires exactly 512 samples for 16kHz
            # Chunk the audio into 512-sample frames and average the results
            chunk_size = 512
            speech_probs = []

            # Process each chunk
            for i in range(0, len(concatenated_frame), chunk_size):
                chunk = concatenated_frame[i : i + chunk_size]

                # Ensure the chunk is exactly 512 samples
                if len(chunk) < chunk_size:
                    # If not enough samples, pad with zeros
                    padded_chunk = np.zeros(chunk_size, dtype=np.float32)
                    padded_chunk[: len(chunk)] = chunk
                    chunk = padded_chunk
                elif len(chunk) > chunk_size:
                    # If too many samples, truncate
                    chunk = chunk[:chunk_size]

                # Convert numpy array to PyTorch tensor
                tensor = torch.from_numpy(chunk).unsqueeze(0).to(self.device)

                # Get model predictions - Silero model requires sample rate as an integer
                with torch.no_grad():
                    try:
                        # The model only needs the tensor and sample rate - older versions used other params
                        speech_prob = self.model(tensor, model_sample_rate)
                        speech_probs.append(float(speech_prob.item()))
                    except Exception as e:
                        logger.warning(f"Error during inference: {e}")
                        # Try with fallback approach if available models
                        try:
                            # Some versions of the model might have different signature
                            speech_prob = self.model(tensor)
                            speech_probs.append(float(speech_prob.item()))
                        except Exception as e2:
                            logger.error(f"Fallback inference failed: {e2}")
                            continue

            # Return highest probability if we have any valid predictions
            return max(speech_probs) if speech_probs else 0.0

        except Exception as e:
            logger.error(f"Error processing audio frame: {e}")
            # On error, return low probability but don't clear the buffer
            return 0.0

    async def reset(self) -> None:
        """Reset the VAD state."""
        await super().reset()
        self.reset_states()

    async def close(self) -> None:
        """Release resources used by the model."""
        self.model = None
        self.audio_buffer = []
