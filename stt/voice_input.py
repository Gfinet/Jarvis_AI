# voice_input.py

import sounddevice as sd
import queue
import sys
import json

from vosk import Model, KaldiRecognizer

from commands import handle_command


def Jarvis():
    sys.stdout.reconfigure(line_buffering=True)

    q = queue.Queue()


    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)

        q.put(bytes(indata))


    # Charge le modèle français
    m_fr = "models/vosk-model-small-fr-0.22"
    print("Chargement du modele", m_fr)
    model = Model(m_fr)
    print("Mdele", m_fr, "chargé")

    # Prépare le recognizer
    print("Chargement du recognizer")
    rec = KaldiRecognizer(model, 16000)
    print("Recognizer chargé")


    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=callback
    ):
        print("Parle maintenant...", flush=True)

        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip()
                print("Tu as dit :", text)
                if text:  # On appelle la commande seulement si du texte est détecté
                    handle_command(text)
            q.queue.clear()