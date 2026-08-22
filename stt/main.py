from threading import Thread, Lock, Event
from queue import Queue

from commands import handle_command
from LLM.llm import AI_resume_msg, AI_translate_user_input
from voice_input import voice_input
from JarvisSpeaker import JarvisSpeaker

def Jarvis():
    speaker = JarvisSpeaker()
    conversation = Queue()
    trad_lock = Lock()
    AI_lock = Lock()
    voice_lock = Lock()

    cancel_event = Event()
    
    voice_lock.acquire()
    trad_lock.acquire()
    AI_lock.acquire()
    t_user = Thread(target=voice_input, args=(conversation, trad_lock, cancel_event), daemon=True)#daemon=True utile?
    t_translate = Thread(target=AI_translate_user_input, args=(conversation, trad_lock, AI_lock, cancel_event))
    t_AI = Thread(target=handle_command, args=(conversation, AI_lock, voice_lock, cancel_event))
    t_resume_AI = Thread(target=AI_resume_msg, args=(conversation, cancel_event))
    
    
    th = [t_user, t_translate, t_AI, t_resume_AI]
    for t in th:
        t.start()

    while (not cancel_event.is_set()):
        if not voice_lock.locked():
            print("AI_VOICE_GO")
            message = conversation.get()
            print("AI msg", message.content)
            speaker.speak(message.content)
            print("Jarvis said")
            conversation.queue.clear()
            voice_lock.acquire()

    print("cancel? ", cancel_event.is_set())
    speaker.speak("À bientôt ! 👋")
    for t in th:
        t.join()
    return

if __name__ == "__main__":
    Jarvis()