# commands.py

import webbrowser
import os
import sys
import subprocess as sb
from threading import Thread, Lock, Event
from queue import Queue

from Jarvis_voice import Jarvis_voice
from LLM.llm import Gemma3

def handle_command(command : Queue, voice_lock: Lock, cancel : Event):
    print("AI_COMMAND")
    while True:    
        if not voice_lock.locked():
            print("AI_COMMAND_GO")
            message = command.get()
            val = Gemma3(message)
            print("Gem rep : ", val.message.content)
            Jarvis_voice(val.message.content)
            if "au revoir" in message:
                cancel.set()
            command.queue.clear()
            voice_lock.acquire()  
        if cancel.is_set():
             break
    # command = command.lower()

    # if "bonjour" in command:
    #     Jarvis_voice(" Bonjour à vous !")

    # elif "ouvre youtube" in command:
    #     Jarvis_voice(" J'ouvre YouTube.")
    #     webbrowser.open("https://www.youtube.com")

    # elif "lance le script" in command:
    #     Jarvis_voice(" Je lance le script.")
    #     sb.call("python3 ton_script.py")

    
        # Jarvis_voice("À bientôt ! 👋")

    # else:
    #     Jarvis_voice(" Je n'ai pas compris cette commande.")


