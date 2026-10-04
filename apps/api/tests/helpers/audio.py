"""Deterministic in-memory audio bytes for tests."""

import io
import struct
import wave


def minimal_wav_bytes(duration_ms: int = 200, sample_rate: int = 16000) -> bytes:
    """Short silent/mono WAV with valid RIFF header."""
    num_samples = int(sample_rate * duration_ms / 1000)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * num_samples)
    return buffer.getvalue()


def fake_mp3_header_bytes() -> bytes:
    """Minimal bytes that pass container sniffing as MP3 (not decodable by STT)."""
    return b"ID3" + b"\x00" * 32 + b"\xff\xfb\x90" + b"\x00" * 64
