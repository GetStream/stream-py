import os
import torchaudio
import torch


def create_test_assets():
    """Create test audio files at different sample rates."""
    # Get the path to the test assets
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(base_dir, "tests", "assets")

    # Input file path
    input_file = os.path.join(assets_dir, "mia.mp3")

    # Output file paths
    output_48k = os.path.join(assets_dir, "speech_48k.wav")
    output_16k = os.path.join(assets_dir, "speech_16k.wav")

    print(f"Loading {input_file}")

    # Load the audio file
    waveform, sample_rate = torchaudio.load(input_file)

    # Check if the audio is too quiet and normalize it if needed
    max_amplitude = torch.max(torch.abs(waveform)).item()
    print(f"Original max amplitude: {max_amplitude:.6f}")

    if max_amplitude < 0.1:
        print("Audio is too quiet, normalizing...")
        # Normalize to have a reasonable volume (peak at around 0.5)
        target_peak = 0.5
        waveform = waveform * (target_peak / max_amplitude)
        print(f"New max amplitude: {torch.max(torch.abs(waveform)).item():.6f}")

    # Create 48 kHz version
    print(f"Creating 48 kHz version: {output_48k}")
    resampler_48k = torchaudio.transforms.Resample(
        orig_freq=sample_rate, new_freq=48000
    )
    resampled_waveform_48k = resampler_48k(waveform)
    torchaudio.save(output_48k, resampled_waveform_48k, sample_rate=48000)
    file_size_48k = os.path.getsize(output_48k) / 1024  # in KB
    print(f"File size: {file_size_48k:.2f} KB")

    # Create 16 kHz version
    print(f"Creating 16 kHz version: {output_16k}")
    resampler_16k = torchaudio.transforms.Resample(
        orig_freq=sample_rate, new_freq=16000
    )
    resampled_waveform_16k = resampler_16k(waveform)
    torchaudio.save(output_16k, resampled_waveform_16k, sample_rate=16000)
    file_size_16k = os.path.getsize(output_16k) / 1024  # in KB
    print(f"File size: {file_size_16k:.2f} KB")

    # Double-check the amplitude of the saved files
    for file_path, desc in [(output_16k, "16kHz"), (output_48k, "48kHz")]:
        wf, sr = torchaudio.load(file_path)
        max_val = torch.max(torch.abs(wf)).item()
        print(f"Saved {desc} file max amplitude: {max_val:.6f}")

    print("Test assets created successfully")

    return output_48k, output_16k


if __name__ == "__main__":
    create_test_assets()
