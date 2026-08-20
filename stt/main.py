from threading import Thread, Lock, Event
from queue import Queue

from commands import handle_command
from LLM.llm import AI_resume_msg, AI_translate_user_input
from voice_input import voice_input


def Jarvis():
    conversation = Queue()
    voice_lock = Lock()
    trad_lock = Lock()
    cancel_event = Event()
    
    voice_lock.acquire()
    trad_lock.acquire()
    t_user = Thread(target=voice_input, args=(conversation, trad_lock, cancel_event), daemon=True)#daemon=True utile?
    t_translate = Thread(target=AI_translate_user_input, args=(conversation, trad_lock, voice_lock, cancel_event))
    t_AI = Thread(target=handle_command, args=(conversation, voice_lock, cancel_event))
    # t_resume_AI = Thread(target=AI_resume_msg, args=(conversation,))
    th = [t_user, t_translate, t_AI] #, t_resume_AI]
    for t in th:
        t.start()
    for t in th:
        t.join()
    # t_user.join()
    # t_translate.join()
    # t_AI.join()
    # t_resume_AI.join()
    return

if __name__ == "__main__":
    Jarvis()