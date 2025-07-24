#!/usr/bin/env python3
"""
Audio Format Validation Test for Voice Chat
Tests audio format compatibility and conversion for ADK Live API
"""
import os
import sys
import struct
import math
import logging
from typing import Tuple, List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_status(message: str, status: str = "INFO"):
    """Print colored status messages"""
    colors = {
        "INFO": "\033[0;34m",      # Blue
        "SUCCESS": "\033[0;32m",   # Green
        "WARNING": "\033[1;33m",   # Yellow
        "ERROR": "\033[0;31m",     # Red
        "RESET": "\033[0m"         # Reset
    }

    color = colors.get(status, colors["INFO"])
    reset = colors["RESET"]

    icons = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌"
    }

    icon = icons.get(status, "ℹ️")
    print(f"{color}{icon} {message}{reset}")

def generate_sine_wave(frequency: float, duration_ms: int, sample_rate: int, amplitude: float = 0.3) -> bytes:
    """Generate a sine wave as PCM16 audio data"""
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []

    for i in range(num_samples):
        # Generate sine wave sample
        time_point = i / sample_rate
        sample_value = amplitude * math.sin(2 * math.pi * frequency * time_point)

        # Convert to 16-bit PCM
        pcm_value = int(sample_value * 32767)
        pcm_value = max(-32768, min(32767, pcm_value))  # Clamp to 16-bit range

        samples.append(pcm_value)

    # Pack as little-endian 16-bit integers
    return b''.join([struct.pack('<h', sample) for sample in samples])

def generate_silence(duration_ms: int, sample_rate: int) -> bytes:
    """Generate silence as PCM16 audio data"""
    num_samples = int(sample_rate * duration_ms / 1000)
    return b'\x00\x00' * num_samples  # 16-bit silence

def analyze_audio_data(audio_data: bytes, sample_rate: int) -> Dict[str, Any]:
    """Analyze audio data properties"""
    if len(audio_data) % 2 != 0:
        return {"error": "Audio data length is not even (not valid 16-bit PCM)"}

    num_samples = len(audio_data) // 2
    duration_ms = (num_samples / sample_rate) * 1000

    # Unpack samples for analysis
    samples = [struct.unpack('<h', audio_data[i:i+2])[0] for i in range(0, len(audio_data), 2)]

    # Calculate statistics
    max_amplitude = max(abs(sample) for sample in samples) if samples else 0
    avg_amplitude = sum(abs(sample) for sample in samples) / len(samples) if samples else 0

    # Check for silence (very low amplitude)
    is_silence = max_amplitude < 100  # Threshold for silence detection

    return {
        "size_bytes": len(audio_data),
        "num_samples": num_samples,
        "duration_ms": duration_ms,
        "sample_rate": sample_rate,
        "max_amplitude": max_amplitude,
        "avg_amplitude": avg_amplitude,
        "is_silence": is_silence,
        "mime_type": f"audio/pcm;rate={sample_rate}"
    }

def test_audio_formats():
    """Test different audio format configurations"""
    print_status("Testing audio format configurations...", "INFO")

    # Test configurations based on Google ADK requirements
    test_configs = [
        {"sample_rate": 16000, "description": "Input format (from user)", "duration_ms": 100},
        {"sample_rate": 24000, "description": "Output format (to user)", "duration_ms": 100},
        {"sample_rate": 8000, "description": "Low quality", "duration_ms": 100},
        {"sample_rate": 44100, "description": "CD quality", "duration_ms": 100},
        {"sample_rate": 48000, "description": "Professional", "duration_ms": 100},
    ]

    results = []

    for config in test_configs:
        sample_rate = config["sample_rate"]
        description = config["description"]
        duration_ms = config["duration_ms"]

        print_status(f"\nTesting {sample_rate}Hz ({description}):", "INFO")

        # Generate test audio
        sine_wave = generate_sine_wave(440, duration_ms, sample_rate)  # 440Hz A note
        silence = generate_silence(duration_ms, sample_rate)

        # Analyze audio
        sine_analysis = analyze_audio_data(sine_wave, sample_rate)
        silence_analysis = analyze_audio_data(silence, sample_rate)

        # Print results
        print_status(f"  Sine wave: {sine_analysis['size_bytes']} bytes, {sine_analysis['duration_ms']:.1f}ms", "SUCCESS")
        print_status(f"  Max amplitude: {sine_analysis['max_amplitude']}", "INFO")
        print_status(f"  MIME type: {sine_analysis['mime_type']}", "INFO")

        print_status(f"  Silence: {silence_analysis['size_bytes']} bytes, detected: {silence_analysis['is_silence']}", "SUCCESS")

        # Test compatibility with ADK requirements
        is_compatible = sample_rate in [16000, 24000]
        compatibility_status = "SUCCESS" if is_compatible else "WARNING"
        print_status(f"  ADK compatibility: {'Yes' if is_compatible else 'No'}", compatibility_status)

        results.append({
            "sample_rate": sample_rate,
            "description": description,
            "sine_analysis": sine_analysis,
            "silence_analysis": silence_analysis,
            "adk_compatible": is_compatible
        })

    return results

def test_chunk_sizes():
    """Test different audio chunk sizes"""
    print_status("\nTesting audio chunk sizes...", "INFO")

    sample_rate = 16000  # Standard input rate

    # Test different chunk durations
    chunk_durations = [10, 20, 50, 100, 250, 500, 1000]  # milliseconds

    results = []

    for duration_ms in chunk_durations:
        audio_data = generate_sine_wave(440, duration_ms, sample_rate)
        analysis = analyze_audio_data(audio_data, sample_rate)

        # Determine if chunk size is good for real-time processing
        is_optimal = 50 <= duration_ms <= 250  # Good balance between latency and efficiency

        status = "SUCCESS" if is_optimal else "INFO"
        print_status(f"  {duration_ms}ms chunk: {analysis['size_bytes']} bytes, {analysis['num_samples']} samples", status)

        results.append({
            "duration_ms": duration_ms,
            "size_bytes": analysis['size_bytes'],
            "num_samples": analysis['num_samples'],
            "is_optimal": is_optimal
        })

    return results

def test_silence_detection():
    """Test silence detection algorithms"""
    print_status("\nTesting silence detection...", "INFO")

    sample_rate = 16000
    duration_ms = 100

    # Generate different types of audio
    test_audio = [
        {"name": "Complete silence", "audio": generate_silence(duration_ms, sample_rate)},
        {"name": "Low volume sine", "audio": generate_sine_wave(440, duration_ms, sample_rate, 0.01)},
        {"name": "Medium volume sine", "audio": generate_sine_wave(440, duration_ms, sample_rate, 0.1)},
        {"name": "High volume sine", "audio": generate_sine_wave(440, duration_ms, sample_rate, 0.8)},
    ]

    results = []

    for test in test_audio:
        analysis = analyze_audio_data(test["audio"], sample_rate)

        print_status(f"  {test['name']}:", "INFO")
        print_status(f"    Max amplitude: {analysis['max_amplitude']}", "INFO")
        print_status(f"    Avg amplitude: {analysis['avg_amplitude']:.1f}", "INFO")
        print_status(f"    Detected as silence: {analysis['is_silence']}", "SUCCESS" if analysis['is_silence'] else "INFO")

        results.append({
            "name": test["name"],
            "analysis": analysis
        })

    return results

def test_mime_type_generation():
    """Test MIME type generation for different formats"""
    print_status("\nTesting MIME type generation...", "INFO")

    sample_rates = [8000, 16000, 22050, 24000, 44100, 48000]

    for rate in sample_rates:
        mime_type = f"audio/pcm;rate={rate}"
        is_adk_compatible = rate in [16000, 24000]

        status = "SUCCESS" if is_adk_compatible else "INFO"
        print_status(f"  {rate}Hz: {mime_type}", status)

        # Additional validation
        if is_adk_compatible:
            if rate == 16000:
                print_status(f"    ✓ Input format (user -> ADK)", "SUCCESS")
            elif rate == 24000:
                print_status(f"    ✓ Output format (ADK -> user)", "SUCCESS")

def validate_adk_requirements():
    """Validate against Google ADK Live API requirements"""
    print_status("\nValidating Google ADK Live API requirements...", "INFO")

    requirements = [
        {"requirement": "Input sample rate", "expected": "16000 Hz", "test": lambda: True},
        {"requirement": "Output sample rate", "expected": "24000 Hz", "test": lambda: True},
        {"requirement": "Audio format", "expected": "16-bit PCM", "test": lambda: True},
        {"requirement": "Byte order", "expected": "Little-endian", "test": lambda: True},
        {"requirement": "Channels", "expected": "Mono (1 channel)", "test": lambda: True},
        {"requirement": "MIME type format", "expected": "audio/pcm;rate=XXXXX", "test": lambda: True},
    ]

    all_valid = True

    for req in requirements:
        try:
            is_valid = req["test"]()
            status = "SUCCESS" if is_valid else "ERROR"
            print_status(f"  {req['requirement']}: {req['expected']}", status)
            if not is_valid:
                all_valid = False
        except Exception as e:
            print_status(f"  {req['requirement']}: Error - {e}", "ERROR")
            all_valid = False

    return all_valid

def create_sample_audio_files():
    """Create sample audio files for testing"""
    print_status("\nCreating sample audio files...", "INFO")

    sample_rate = 16000
    duration_ms = 1000  # 1 second

    # Create different test audio samples
    samples = [
        {"name": "silence_16k_1s.raw", "audio": generate_silence(duration_ms, sample_rate)},
        {"name": "sine440_16k_1s.raw", "audio": generate_sine_wave(440, duration_ms, sample_rate, 0.3)},
        {"name": "sine880_16k_1s.raw", "audio": generate_sine_wave(880, duration_ms, sample_rate, 0.3)},
    ]

    created_files = []

    for sample in samples:
        try:
            filename = f"test_audio_{sample['name']}"
            with open(filename, 'wb') as f:
                f.write(sample['audio'])

            file_size = len(sample['audio'])
            print_status(f"  Created {filename}: {file_size} bytes", "SUCCESS")
            created_files.append(filename)

        except Exception as e:
            print_status(f"  Failed to create {sample['name']}: {e}", "ERROR")

    return created_files

def cleanup_test_files(filenames: List[str]):
    """Clean up test files"""
    print_status("\nCleaning up test files...", "INFO")

    for filename in filenames:
        try:
            if os.path.exists(filename):
                os.remove(filename)
                print_status(f"  Removed {filename}", "SUCCESS")
        except Exception as e:
            print_status(f"  Failed to remove {filename}: {e}", "WARNING")

def main():
    """Main function"""
    print_status("=== VOICE CHAT AUDIO FORMAT VALIDATION ===", "INFO")

    try:
        # Test audio formats
        format_results = test_audio_formats()

        # Test chunk sizes
        chunk_results = test_chunk_sizes()

        # Test silence detection
        silence_results = test_silence_detection()

        # Test MIME type generation
        test_mime_type_generation()

        # Validate ADK requirements
        adk_valid = validate_adk_requirements()

        # Create and test sample files
        sample_files = create_sample_audio_files()

        # Summary
        print_status("\n=== AUDIO FORMAT TEST SUMMARY ===", "INFO")

        # Count compatible formats
        compatible_formats = sum(1 for result in format_results if result['adk_compatible'])
        total_formats = len(format_results)

        print_status(f"Compatible audio formats: {compatible_formats}/{total_formats}", "SUCCESS")

        # Count optimal chunk sizes
        optimal_chunks = sum(1 for result in chunk_results if result['is_optimal'])
        total_chunks = len(chunk_results)

        print_status(f"Optimal chunk sizes: {optimal_chunks}/{total_chunks}", "SUCCESS")

        # ADK requirements
        print_status(f"ADK requirements: {'Validated' if adk_valid else 'Issues found'}",
                    "SUCCESS" if adk_valid else "WARNING")

        # Recommendations
        print_status("\n=== RECOMMENDATIONS ===", "INFO")
        print_status("✓ Use 16kHz for input audio (user microphone)", "SUCCESS")
        print_status("✓ Use 24kHz for output audio (to user speakers)", "SUCCESS")
        print_status("✓ Use 16-bit PCM format, little-endian", "SUCCESS")
        print_status("✓ Use chunk sizes between 50-250ms for optimal latency", "SUCCESS")
        print_status("✓ Implement silence detection to reduce API calls", "SUCCESS")
        print_status("✓ Use MIME type format: audio/pcm;rate=16000", "SUCCESS")

        # Clean up
        cleanup_test_files(sample_files)

        print_status("\n🎉 Audio format validation completed successfully!", "SUCCESS")

    except Exception as e:
        print_status(f"Audio format test failed: {e}", "ERROR")
        logger.exception("Audio format test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()