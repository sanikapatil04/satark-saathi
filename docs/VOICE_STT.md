# Voice analysis (Phase 3)

## Endpoint

`POST /api/v1/voice/analyze` (multipart)

| Field | Description |
|-------|-------------|
| `audio` | WAV, MP3, WebM, OGG, or M4A (max 10 MB default) |
| `language` | Optional: `en`, `hi`, `mr`, or `auto` (default) |

## Speech-to-text

- **Engine:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (local, CPU)
- **Default model:** `tiny` (multilingual, ~75MB download on first run)
- **Install:** `pip install ".[voice]"` from `apps/api`
- **Docker API image:** installs `.[voice]` and `ffmpeg`

Audio is processed in a temporary file and deleted after transcription. Transcripts are not logged by the STT service.

## Spoken response

The API returns `spoken_response` as **text**. The web test page uses browser `SpeechSynthesis` to read it aloud. Hindi/Marathi TTS voices depend on the user’s device and are not guaranteed.

## Language support

| Language | STT hint | Verified in CI |
|----------|----------|----------------|
| English | `en` or `auto` | Mocked API tests |
| Hindi | `hi` | Unicode transcript via mocked STT |
| Marathi | `mr` | Unicode transcript via mocked STT |

Real Hindi/Marathi **audio** recognition must be verified separately on a machine with `faster-whisper` installed (see `tests/integration/test_voice_real_stt.py` if present).
