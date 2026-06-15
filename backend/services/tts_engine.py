# backend/services/tts_engine.py

import os
from kokoro_onnx import Kokoro

MODEL_PATH = os.getenv("KOKORO_MODEL_PATH", "models/kokoro-v1.0.onnx")
VOICES_PATH = os.getenv("KOKORO_VOICES_PATH", "models/voices-v1.0.bin")

class KokoroEngine:
    _instance = None
    _missing_logged = False

    @classmethod
    def get(cls):
        if cls._instance is None:
            if os.path.exists(MODEL_PATH) and os.path.exists(VOICES_PATH):
                print("[TTS] HARD INIT KokoroTTS ONCE")
                cls._instance = Kokoro(MODEL_PATH, VOICES_PATH)
                print("[TTS] Kokoro loaded successfully")
            else:
                if not cls._missing_logged:
                    print("[TTS WARNING] Model or voices missing — TTS disabled")
                    cls._missing_logged = True
        return cls._instance