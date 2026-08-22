# commands.py

import webbrowser
import os
import sys
import subprocess as sb
from threading import Thread, Lock, Event
from queue import Queue

from LLM.llm import Gemma3

def handle_command(command : Queue, AI_lock: Lock, voice_lock: Lock, cancel : Event):
    print("AI_COMMAND")
    while True:    
        if not AI_lock.locked():
            print("AI_COMMAND_GO")
            message = command.get()
            print("Gemma in : ", message["content"])
            val = Gemma3(message["content"])
            command.queue.clear()
            command.put(val.message)
            voice_lock.release()
            print("Gem rep : ", val.message["content"])
            if ("au revoir" in message) or ("Au revoir." in message):
                cancel.set()
            AI_lock.acquire()
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


