"""Text-to-speech boundary (Phase 3: backend returns text; client speaks it).

Browser playback uses ``window.speechSynthesis`` on the web test page.
Language-specific Hindi/Marathi voices depend on the user device and are not
guaranteed by this API.
"""


def playback_hint() -> str:
    return (
        "Use the spoken_response field with browser SpeechSynthesis or a future "
        "local TTS adapter. No external paid TTS APIs are used in Phase 3."
    )
