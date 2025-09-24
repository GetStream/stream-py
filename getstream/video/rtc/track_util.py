import asyncio

import av
import numpy as np
import re
from typing import Dict, Any, NamedTuple, Callable, Optional

import logging
import aiortc
from aiortc import MediaStreamTrack
from aiortc.mediastreams import MediaStreamError
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class PcmData(NamedTuple):
    """
    A named tuple representing PCM audio data.

    Attributes:
        format: The format of the audio data.
        sample_rate: The sample rate of the audio data.
        samples: The audio samples as a numpy array.
        pts: The presentation timestamp of the audio data.
        dts: The decode timestamp of the audio data.
        time_base: The time base for converting timestamps to seconds.
    """

    format: str
    sample_rate: int
    samples: NDArray
    pts: Optional[int] = None  # Presentation timestamp
    dts: Optional[int] = None  # Decode timestamp
    time_base: Optional[float] = None  # Time base for converting timestamps to seconds

    @property
    def duration(self) -> float:
        """
        Calculate the duration of the audio data in seconds.

        Returns:
            float: Duration in seconds.
        """
        # The samples field contains a numpy array of audio samples
        # For s16 format, each element in the array is one sample (int16)
        # For f32 format, each element in the array is one sample (float32)

        if isinstance(self.samples, np.ndarray):
            # Direct count of samples in the numpy array
            num_samples = len(self.samples)
        elif isinstance(self.samples, bytes):
            # If samples is bytes, calculate based on format
            if self.format == "s16":
                # For s16 format, each sample is 2 bytes (16 bits)
                num_samples = len(self.samples) // 2
            elif self.format == "f32":
                # For f32 format, each sample is 4 bytes (32 bits)
                num_samples = len(self.samples) // 4
            else:
                # Default assumption for other formats (treat as raw bytes)
                num_samples = len(self.samples)
        else:
            # Fallback: try to get length
            try:
                num_samples = len(self.samples)
            except TypeError:
                logger.warning(
                    f"Cannot determine sample count for type {type(self.samples)}"
                )
                return 0.0

        # Calculate duration based on sample rate
        return num_samples / self.sample_rate

    @property
    def pts_seconds(self) -> Optional[float]:
        if self.pts is not None and self.time_base is not None:
            return self.pts * self.time_base
        return None

    @property
    def dts_seconds(self) -> Optional[float]:
        if self.dts is not None and self.time_base is not None:
            return self.dts * self.time_base
        return None


def patch_sdp_offer(sdp: str) -> str:
    """
    Patches an SDP offer to ensure consistent ICE and DTLS parameters across all media sections.

    This function:
    1. Ensures all media descriptions have the same ice-ufrag, ice-pwd, and fingerprint values
       (using values from the first media section)
    2. Sets all media descriptions' ports to match the first media description's port
    3. Replaces all media descriptions' candidates with candidates from the first media description

    Args:
        sdp: The original SDP string.

    Returns:
        The modified SDP string with consistent parameters across all media sections.
    """
    # Parse the SDP
    session = aiortc.sdp.SessionDescription.parse(sdp)

    # If we have fewer than 2 media sections, nothing to patch
    if len(session.media) < 2:
        return sdp

    # Get the values from the first media section
    first_media = session.media[0]
    reference_port = first_media.port
    reference_ice = first_media.ice
    reference_fingerprints = first_media.dtls.fingerprints if first_media.dtls else []
    reference_candidates = first_media.ice_candidates

    # Apply to all other media sections
    for media in session.media[1:]:
        # Update port
        media.port = reference_port

        # Update ICE parameters
        if reference_ice:
            media.ice.usernameFragment = reference_ice.usernameFragment
            media.ice.password = reference_ice.password
            media.ice.iceLite = reference_ice.iceLite

        # Update DTLS fingerprints
        if media.dtls and reference_fingerprints:
            media.dtls.fingerprints = reference_fingerprints.copy()

        # Replace ICE candidates
        media.ice_candidates = reference_candidates.copy()
        if reference_candidates:
            media.ice_candidates_complete = True

    # Convert back to string
    return str(session)


def fix_sdp_msid_semantic(sdp: str) -> str:
    """
    Fix SDP msid-semantic format by ensuring there is a space after "WMS".

    The WebRTC spec requires a space between "WMS" and any identifiers.
    Some SDPs may incorrectly have "WMS*" instead of "WMS *" which can
    cause connection issues.

    Args:
        sdp: The SDP string to fix

    Returns:
        The fixed SDP string
    """
    return re.sub(r"a=msid-semantic:WMS\*", r"a=msid-semantic:WMS *", sdp)


def fix_sdp_rtcp_fb(sdp: str) -> str:
    """
    Fix SDP rtcp-fb format
    https://github.com/pion/webrtc/issues/3207
    """
    # Some generators (e.g. pion) emit a trailing space after feedback id when no
    # parameter is present, e.g. "a=rtcp-fb:96 goog-remb ". This breaks some
    # parsers. Strip only the trailing whitespace before end-of-line on rtcp-fb
    # lines while preserving CRLF if present.
    #
    # Example fix:
    #   a=rtcp-fb:96 goog-remb \r\n  ->  a=rtcp-fb:96 goog-remb\r\n
    return re.sub(
        r"(?m)^(a=rtcp-fb:[^\r\n]*\S)[ \t]+(?=\r?$)",
        r"\1",
        sdp,
    )


def parse_track_stream_mapping(sdp: str) -> dict:
    """Parse SDP to extract track_id to stream_id mapping from msid lines."""
    mapping = {}
    for line in sdp.split("\n"):
        if line.startswith("a=msid:"):
            parts = line.strip().split(" ")
            if len(parts) >= 2:
                # Format: a=msid:stream_id track_id
                track_id = parts[1]
                stream_id = parts[0].replace("a=msid:", "")
                mapping[track_id] = stream_id
    return mapping


class BufferedMediaTrack(aiortc.mediastreams.MediaStreamTrack):
    """A wrapper for MediaStreamTrack that buffers one peeked frame."""

    def __init__(self, track):
        super().__init__()
        self._track = track
        self._buffered_frames = []  # Store multiple frames
        self._kind = track.kind
        self._id = track.id
        self._ended = False

    @property
    def kind(self):
        return self._kind

    @property
    def id(self):
        return self._id

    @property
    def readyState(self):
        return "ended" if self._ended else self._track.readyState

    async def recv(self):
        """Returns the next buffered frame if available, otherwise gets a new frame from the track."""
        if self._ended:
            raise MediaStreamError("Track is ended")

        if self._buffered_frames:
            # Return the oldest buffered frame (FIFO order)
            return self._buffered_frames.pop(0)

        try:
            return await self._track.recv()
        except Exception as e:
            logger.error(f"Error receiving frame from track: {e}")
            self._ended = True
            raise MediaStreamError(f"Error receiving frame: {e}") from e

    async def peek(self):
        """Peek at the next frame without removing it from the stream."""
        if self._ended:
            raise MediaStreamError("Track is ended")

        if not self._buffered_frames:
            try:
                # Buffer a new frame
                frame = await self._track.recv()
                self._buffered_frames.append(frame)
            except Exception as e:
                logger.error(f"Error peeking at frame: {e}")
                self._ended = True
                raise MediaStreamError(f"Error peeking at frame: {e}") from e

        # Return the next frame that would be received, but don't remove it
        if self._buffered_frames:
            return self._buffered_frames[0]
        return None

    def stop(self):
        """Stop the track and clean up resources."""
        if not self._ended:
            self._ended = True
            self._buffered_frames = []  # Clear all buffered frames
            # Stop the underlying track if it has a stop method
            if hasattr(self._track, "stop"):
                try:
                    self._track.stop_audio()
                except Exception as e:
                    logger.error(f"Error stopping track: {e}")


async def detect_video_properties(
    video_track: aiortc.mediastreams.MediaStreamTrack,
) -> Dict[str, Any]:
    """
    Detect video track properties by peeking at frames.

    Args:
        video_track: A video MediaStreamTrack

    Returns:
        Dict containing width (int), height (int), fps (int), and bitrate (int) in kbps
    """
    logger.info("Detecting video track properties")

    # Default properties in case of failure
    default_properties = {"width": 640, "height": 480, "fps": 30, "bitrate": 800}

    if not video_track or video_track.kind != "video":
        logger.warning("No video track provided or track is not video")
        return default_properties

    # Flag to indicate if we created our own buffered track
    own_buffered_track = False
    buffered_track = None

    try:
        # Ensure we're using a buffered track
        if isinstance(video_track, BufferedMediaTrack):
            buffered_track = video_track
        else:
            buffered_track = BufferedMediaTrack(video_track)
            own_buffered_track = True

        # Peek at a frame to get dimensions
        frame1 = await asyncio.wait_for(buffered_track.peek(), timeout=2.0)

        if not frame1:
            logger.warning("No frame received from video track")
            return default_properties

        # Extract width and height
        width = getattr(frame1, "width", default_properties["width"])
        height = getattr(frame1, "height", default_properties["height"])

        # Calculate FPS based on time delta between consecutive frames
        fps = 30  # Default value
        try:
            # Consume the first frame but store its pts and time_base
            frame1 = await buffered_track.recv()
            frame1_pts = getattr(frame1, "pts", None)
            time_base = getattr(frame1, "time_base", None)

            # Get the second frame
            frame2 = await asyncio.wait_for(buffered_track.recv(), timeout=2.0)
            frame2_pts = getattr(frame2, "pts", None)

            # Calculate FPS if we have all the necessary information
            if (
                frame1_pts is not None
                and frame2_pts is not None
                and time_base is not None
            ):
                delta_ticks = frame2_pts - frame1_pts
                delta_seconds = delta_ticks * time_base

                if delta_seconds > 0:
                    estimated_fps = 1 / delta_seconds
                    fps = int(round(estimated_fps))
                    logger.info(f"Calculated FPS: {fps} (delta: {delta_seconds}s)")
                else:
                    logger.warning("Cannot calculate FPS: zero or negative time delta")
            else:
                logger.warning(
                    "Cannot calculate FPS: missing PTS or time_base information"
                )
        except Exception as e:
            logger.warning(f"Error calculating FPS: {e}, using default 30 fps")

        # Calculate a dynamic bitrate based on resolution and fps
        # This formula accounts for both pixel count and frame rate
        # Using bits-per-pixel approach for H.264 encoding
        pixels_per_second = width * height * fps

        # Different quality factors based on resolution
        if width >= 1920 and height >= 1080:  # Full HD
            # Higher quality for HD content: ~0.1 bits per pixel
            bits_per_pixel = 0.1
        elif width >= 1280 and height >= 720:  # HD
            # Medium-high quality: ~0.08 bits per pixel
            bits_per_pixel = 0.08
        elif width >= 854 and height >= 480:  # SD
            # Medium quality: ~0.06 bits per pixel
            bits_per_pixel = 0.06
        else:  # Lower quality
            # Lower quality for smaller video: ~0.05 bits per pixel
            bits_per_pixel = 0.05

        # Calculate bitrate in kbps
        estimated_bitrate = int(pixels_per_second * bits_per_pixel / 1000)

        # Set reasonable min/max boundaries
        min_bitrate = 100  # Minimum acceptable bitrate
        max_bitrate = 5000  # Maximum reasonable bitrate for WebRTC

        bitrate = max(min_bitrate, min(estimated_bitrate, max_bitrate))

        logger.info(f"Detected video properties: {width}x{height} at {fps}fps")
        logger.info(
            f"Calculated bitrate: {bitrate} kbps (based on {bits_per_pixel} bits/pixel)"
        )

        return {"width": width, "height": height, "fps": fps, "bitrate": bitrate}
    except asyncio.TimeoutError:
        logger.error("Timeout while waiting for video frame")
        return default_properties
    except Exception as e:
        logger.error(f"Error detecting video properties: {e}")
        return default_properties
    finally:
        # Clean up only if we created our own buffered track
        if own_buffered_track and buffered_track:
            try:
                # Clean up the buffered track but don't stop the original track
                buffered_track._buffered_frames = []
                buffered_track._ended = True
            except Exception as e:
                logger.error(f"Error cleaning up buffered track: {e}")


class AudioTrackHandler:
    """
    A helper to receive raw PCM data from an aiortc AudioStreamTrack
    and feed it into the provided callback.
    """

    def __init__(
        self, track: MediaStreamTrack, on_audio_frame: Callable[[PcmData], Any]
    ):
        """
        :param track: The incoming audio track (from `pc.on("track")`).
        :param on_audio_frame: A callback function that will receive
                               the PCM data as a NumPy array (int16).
        """
        self.track = track
        self._on_audio_frame = on_audio_frame
        self._task = None
        self._stopped = False

    async def start(self):
        """
        Start reading frames from the track in a background task.
        """
        if self._task is None:
            self._task = asyncio.create_task(self._run_track())

    async def stop(self):
        """
        Stop reading frames and clean up.
        """
        self._stopped = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run_track(self):
        """
        Internal coroutine that continuously pulls frames from the track.
        """

        while not self._stopped:
            try:
                frame = await self.track.recv()
            except asyncio.CancelledError:
                # Task was cancelled, safe to exit
                break
            except MediaStreamError:
                # Error with the media stream, possibly EOF
                break
            except Exception as e:
                logger.error(f"Error receiving audio frame: {e}")
                break

            if not isinstance(frame, av.AudioFrame):
                raise TypeError("Audio frame not received")

            if frame.sample_rate != 48000:
                raise TypeError("only 48000 sample rate supported")

            try:
                pcm_ndarray = frame.to_ndarray()
            except Exception as plane_error:
                logger.error(
                    f"Error converting audio frame to ndarray: {plane_error}, dropping frame"
                )
                break

            # Handle stereo to mono conversion
            if len(frame.layout.channels) > 1:
                try:
                    # Reshape to separate stereo channels: [L, R, L, R, ...] -> [[L, R], [L, R], ...]
                    # This assumes the data is interleaved stereo
                    audio_stereo = pcm_ndarray.reshape(-1, len(frame.layout.channels))
                    # Take the mean across channels to convert to mono
                    pcm_ndarray = audio_stereo.mean(axis=1).astype(np.int16)
                except ValueError as e:
                    logger.error(
                        f"Error reshaping stereo audio: {e}. "
                        f"Original shape: {pcm_ndarray.shape}, channels: {len(frame.layout.channels)}"
                    )
                    break

            # Extract timestamp information from the frame
            pts = getattr(frame, "pts", None)
            dts = getattr(frame, "dts", None)
            time_base = None

            # Convert time_base to float if available
            if hasattr(frame, "time_base") and frame.time_base is not None:
                try:
                    # time_base is typically a fractions.Fraction, convert to float
                    time_base = float(frame.time_base)
                except (TypeError, ValueError):
                    logger.warning(
                        f"Could not convert time_base to float: {frame.time_base}"
                    )
                    time_base = None

            self._on_audio_frame(
                PcmData(
                    sample_rate=48_000,
                    samples=pcm_ndarray,
                    format="s16",
                    pts=pts,
                    dts=dts,
                    time_base=time_base,
                )
            )
