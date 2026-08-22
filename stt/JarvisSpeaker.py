
import logging
import hashlib
import os
import sys
import wave
from pathlib import Path

from dotenv import load_dotenv
import numpy as np
import sounddevice as sd

TARGET_SAMPLE_RATE = 44100

JARVIS_WELCOME_ENABLED = True
JARVIS_WELCOME_PHRASE = (
    "Bienvenue a la maison, Monsieur."
    "J'espere que la journée a été bonne."
)

# Seconds after launching SONG_URI before speaking (gives Spotify/browser time to start).
JARVIS_AFTER_SONG_DELAY_S = 3.0
# Save ElevenLabs PCM as WAV under .cache/jarvis_welcome/; replay skips the API when the key matches.
JARVIS_WELCOME_CACHE_ENABLED = True

load_dotenv(Path(__file__).resolve().parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("clap_listen")


def _play_audio_array(pcm_f: np.ndarray, orig_rate: int) -> bool:
    try:
        # 1. Alignement strict de la mémoire
        audio_data = np.ascontiguousarray(pcm_f, dtype=np.float32)

        # 2. Utilisation d'un flux de sortie explicite et isolé
        # Remplace sd.play() pour éviter les conflits de tampon avec le micro
        with sd.OutputStream(
            samplerate=orig_rate,
            channels=1,
            dtype='float32',
            blocksize=2048  # Réserve une taille de buffer fixe et stable pour le thread
        ) as stream:
            stream.write(audio_data)

        return True
    except Exception as e:
        log.warning("Could not play audio via OutputStream: %s", e)
        return False

def _elevenlabs_pcm_sample_rate(output_format: str) -> int:
    override = (os.environ.get("ELEVENLABS_PCM_SAMPLE_RATE") or "").strip()
    if override.isdigit():
        return int(override)
    if output_format.startswith("pcm_"):
        try:
            return int(output_format.split("_", maxsplit=1)[1])
        except (ValueError, IndexError):
            pass
    return 24000

def _jarvis_welcome_cache_dir() -> Path:
    base = Path(__file__).resolve().parent
    override = (os.environ.get("JARVIS_WELCOME_CACHE_DIR") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return base / ".cache" / "jarvis_welcome"


def _jarvis_welcome_cache_path(
    text: str, voice_id: str, model_id: str, output_format: str
) -> Path:
    key = f"{text}|{voice_id}|{model_id}|{output_format}".encode()
    digest = hashlib.sha256(key).hexdigest()[:24]
    return _jarvis_welcome_cache_dir() / f"{digest}.wav"


def _play_pcm_wav_file(path: Path) -> bool:
    try:
        with wave.open(str(path), "rb") as wf:
            ch = wf.getnchannels()
            sw = wf.getsampwidth()
            rate = wf.getframerate()
            if ch != 1 or sw != 2:
                log.warning("Unsupported cached WAV (channels=%s, width=%s).", ch, sw)
                return False
            raw = wf.readframes(wf.getnframes())
    except (OSError, wave.Error) as e:
        log.warning("Could not read cached welcome audio: %s", e)
        return False
    if not raw:
        return False
    # pcm_i16 = np.frombuffer(raw, dtype=np.int16)
    # pcm_f = pcm_i16.astype(np.float32) / 32768.0
    pcm_i16 = np.frombuffer(raw, dtype="<i2")  # Explicit Int16 Little-Endian
    pcm_f = pcm_i16.astype(np.float32) / 32768.0
    return _play_audio_array(pcm_f, rate)
    try:
        sd.play(pcm_f, rate)
        sd.wait()
    except Exception as e:
        log.warning("Could not play cached welcome audio: %s", e)
        return False
    return True


def _save_pcm_wav_file(path: Path, pcm_bytes: bytes, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with wave.open(str(tmp), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        tmp.replace(path)
    except OSError:
        if tmp.is_file():
            tmp.unlink(missing_ok=True)
        raise

# À la place des fonctions elevenlabs_env_config et Jarvis_voice :

class JarvisSpeaker:
    def __init__(self):
        self.vid, self.model_id, self.output_format, self.pcm_rate = self._load_config()
        self.api_key = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
        self.client = None

        if not self.vid:
            log.warning("Set ELEVENLABS_VOICE_ID in the environment.")
        if not self.api_key:
            log.warning("Set ELEVENLABS_API_KEY in the environment.")
        else:
            try:
                from elevenlabs.client import ElevenLabs
                # Le client est initialisé UNE SEULE FOIS ici au démarrage
                self.client = ElevenLabs(api_key=self.api_key)
            except ImportError:
                log.warning("Install dependencies: pip install -r requirements.txt")

    def _load_config(self) -> tuple[str, str, str, int]:
        voice = (os.environ.get("ELEVENLABS_VOICE_ID") or "").strip()
        model = (os.environ.get("ELEVENLABS_MODEL_ID") or "eleven_multilingual_v2").strip()
        fmt = (os.environ.get("ELEVENLABS_OUTPUT_FORMAT") or "pcm_24000").strip()
        rate = _elevenlabs_pcm_sample_rate(fmt)
        return voice, model, fmt, rate

    def speak(self, sentence: str) -> None:
        if not sentence.strip():
            return
        text = sentence.strip()

        # 1. Vérification du cache (identique)
        cache_path = _jarvis_welcome_cache_path(text, self.vid, self.model_id, self.output_format)
        if JARVIS_WELCOME_CACHE_ENABLED and cache_path.is_file():
            log.info("Playing text from cache: %s", cache_path)
            if _play_pcm_wav_file(cache_path):
                return
            log.warning("Cache miss after read failure; fetching from ElevenLabs.")

        if not self.client or not self.vid:
            log.warning("ElevenLabs client or Voice ID not configured properly.")
            return

        # 2. Appel TTS réutilisant l'instance déjà prête
        try:
            chunks = self.client.text_to_speech.convert(
                voice_id=self.vid,
                text=text,
                model_id=self.model_id,
                output_format=self.output_format,
            )
            raw = b"".join(chunks)
        except Exception as e:
            log.warning("ElevenLabs TTS failed: %s", e)
            return

        if not raw:
            log.warning("ElevenLabs returned empty audio.")
            return

        if JARVIS_WELCOME_CACHE_ENABLED:
            try:
                _save_pcm_wav_file(cache_path, raw, self.pcm_rate)
                log.info("Saved welcome audio to cache: %s", cache_path)
            except OSError as e:
                log.warning("Could not save welcome cache: %s", e)

        pcm_i16 = np.frombuffer(raw, dtype="<i2")
        pcm_f = pcm_i16.astype(np.float32) / 32768.0
        _play_audio_array(pcm_f, self.pcm_rate)
