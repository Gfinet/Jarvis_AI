import time
import numpy as np
import sounddevice as sd
from pywhispercpp.model import Model  # type: ignore

from queue import Queue, Empty
from threading import Lock, Event

SAMPLE_RATE = 16000
CHANNELS = 1

# BAISSE RADICALE du seuil. Sur Mac, la voix normale se situe souvent autour de 0.002
SILENCE_THRESHOLD = 0.002  
SILENCE_DURATION = 1.2     
# On convertit le temps de silence en nombre strict d'échantillons audio
SILENCE_FRAMES_LIMIT = int(SILENCE_DURATION * SAMPLE_RATE)

def voice_input(content: Queue, trad_lock: Lock, cancel: Event):
    print("VOICE_INPUT")
    model = Model('base', language='fr', n_threads=4, redirect_whispercpp_logs_to=None)
    print("Whisper.cpp prêt ! Écoute en cours...")

    audio_buffer = []
    is_speaking = False
    silence_frames = 0  # <-- On ne se fie plus à l'horloge, on compte les frames !
    
    phrase_queue = Queue()

    def callback(indata, frames, time_info, status):
        nonlocal is_speaking, silence_frames, audio_buffer
        if cancel.is_set():
            return
            
        rms = np.sqrt(np.mean(indata**2))

        # Décommentez les deux lignes ci-dessous pour voir le volume réel de votre voix
        # if rms > 0.001:
        #     print(f"Volume actuel: {rms:.4f}")

        if rms > SILENCE_THRESHOLD:
            is_speaking = True
            silence_frames = 0
            audio_buffer.append(indata.copy())
        elif is_speaking:
            silence_frames += frames
            audio_buffer.append(indata.copy())
            
            # On coupe SEULEMENT quand on a réellement accumulé 1.2s d'audio vide
            if silence_frames > SILENCE_FRAMES_LIMIT:
                is_speaking = False
                phrase_queue.put(audio_buffer.copy())
                audio_buffer.clear()
                silence_frames = 0

    # On impose un blocksize=2048 pour forcer le Mac à envoyer des paquets réguliers
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32', blocksize=2048, callback=callback):
        while not cancel.is_set():
            try:
                # timeout=0.2 agit comme un time.sleep() intelligent
                to_process = phrase_queue.get(timeout=0.2)
            except Empty:
                continue

            print("buffering")
            audio_data = np.concatenate(to_process, axis=0).flatten()
            duration = len(audio_data) / SAMPLE_RATE

            if len(audio_data) < SAMPLE_RATE * 0.4:
                print(f"yolo (bruit ignoré: {duration:.2f}s au lieu de 0.4s)")
                continue

            if len(audio_data) < SAMPLE_RATE:
                padding = np.zeros(SAMPLE_RATE - len(audio_data), dtype=np.float32)
                audio_data = np.concatenate([audio_data, padding])

            print(f"Analyse de {duration:.1f}s d'audio...")
            segments = model.transcribe(audio_data, initial_prompt="Jarvis, voici une commande pour toi")
            jarvis_aliases = ["j'arvisse", "jarvisse", "jarvises", "j'avis", "jarvis", "j'arvis", "charvis", "charvisse", "J'avis", "j'arvisent", "j'ai harvies"]
            # segments = model.transcribe(audio_data)
            full_text = " ".join([segment.text for segment in segments]).strip()

            if full_text in ["[Musique]", "[Silence]", "(musique)", "Sous-titres réalisés par...", ""]:
                continue

            clean_text = full_text.lower()
            print(f"clean : '{clean_text}'")
            if clean_text and any(alias in clean_text[:20] for alias in jarvis_aliases):                
                for alias in jarvis_aliases:
                    if alias in clean_text:
                        full_text = full_text.lower().replace(alias, "jarvis", 1)
                        break
                clean_text = full_text.lower()
            print(f"Entendu : '{full_text}'")
            print("if ", not (clean_text == None), "and", "jarvis" in clean_text[:15], clean_text and "jarvis" in clean_text[:15], clean_text[:15])
            if clean_text and "jarvis" in clean_text[:15]:
                print(f"--> Commande acceptée : {full_text}")
                content.queue.clear()
                content.put({'role': 'user', 'content': full_text})
                if trad_lock.locked():
                    trad_lock.release()