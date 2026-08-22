import time
import numpy as np
import sounddevice as sd
from pywhispercpp.model import Model  # type: ignore

from queue import Queue, Empty
from threading import Lock, Event

SAMPLE_RATE = 16000
CHANNELS = 1
SILENCE_THRESHOLD = 0.006  
SILENCE_DURATION = 1.2     

def voice_input(content: Queue, trad_lock: Lock, cancel: Event):
    print("VOICE_INPUT")
    model = Model('base', language='fr', n_threads=4)
    print("Whisper.cpp prêt ! Écoute en cours...")

    audio_buffer = []
    is_speaking = False
    last_voice_time = time.time()
    
    # Nouvelle file d'attente ultra-sécurisée entre le micro et l'analyse
    phrase_queue = Queue()

    def callback(indata, frames, time_info, status):
        nonlocal is_speaking, last_voice_time, audio_buffer
        if cancel.is_set():
            return
            
        if status:
            print(f"Attention micro: {status}")

        rms = np.sqrt(np.mean(indata**2))

        if rms > SILENCE_THRESHOLD:
            if not is_speaking:
                is_speaking = True
            last_voice_time = time.time()
            audio_buffer.append(indata.copy())
        elif is_speaking:
            audio_buffer.append(indata.copy())
            # Dès que le silence d'1.2s est atteint, ON FERME LA PHRASE
            if time.time() - last_voice_time > SILENCE_DURATION:
                is_speaking = False
                # On pousse tout le bloc dans la queue et on vide proprement
                phrase_queue.put(audio_buffer.copy())
                audio_buffer.clear()

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32', callback=callback):
        while not cancel.is_set():
            try:
                # Attend patiemment qu'une phrase complète soit déposée (timeout court pour vérifier le cancel_event)
                to_process = phrase_queue.get(timeout=0.2)
            except Empty:
                continue

            print("buffering")
            audio_data = np.concatenate(to_process, axis=0).flatten()
            duration = len(audio_data) / SAMPLE_RATE

            # Votre garde fou "yolo", maintenant avec des infos de débug !
            if len(audio_data) < SAMPLE_RATE * 0.4:
                print(f"yolo (bruit ignoré: {duration:.2f}s au lieu de 0.4s)")
                continue

            # PADDING : Whisper a besoin d'au moins 1 seconde pour être performant
            if len(audio_data) < SAMPLE_RATE:
                padding = np.zeros(SAMPLE_RATE - len(audio_data), dtype=np.float32)
                audio_data = np.concatenate([audio_data, padding])

            print(f"Analyse de {duration:.1f}s d'audio...")
            segments = model.transcribe(audio_data)
            full_text = " ".join([segment.text for segment in segments]).strip()

            if full_text in ["[Musique]", "[Silence]", "(musique)", "Sous-titres réalisés par...", ""]:
                continue

            print(f"Entendu : '{full_text}'")

            clean_text = full_text.lower()
            if clean_text and "jarvis" in clean_text[:15]:
                print(f"--> Commande acceptée : {full_text}")
                content.put({'role': 'user', 'content': full_text})
                if trad_lock.locked():
                    trad_lock.release()