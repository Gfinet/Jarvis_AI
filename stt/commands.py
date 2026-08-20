# commands.py

import webbrowser
import os
import sys
import subprocess as sb

from Jarvis_voice import Jarvis_voice
from LLM.llm import Gemma3

def handle_command(command):
    val = Gemma3(command)
    Jarvis_voice(val.message.content)
    print("val", val)
    # command = command.lower()

    # if "bonjour" in command:
    #     Jarvis_voice(" Bonjour à vous !")

    # elif "ouvre youtube" in command:
    #     Jarvis_voice(" J'ouvre YouTube.")
    #     webbrowser.open("https://www.youtube.com")

    # elif "lance le script" in command:
    #     Jarvis_voice(" Je lance le script.")
    #     sb.call("python3 ton_script.py")

    if "au revoir" in command:
        # Jarvis_voice("À bientôt ! 👋")
        sys.exit(0)

    # else:
    #     Jarvis_voice(" Je n'ai pas compris cette commande.")
