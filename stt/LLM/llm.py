import ollama
from threading import Thread, Lock, Event
from queue import Queue

Jarvis_history = [
	{
	"role": "system",
	"content": "Tu es Jarvis, un assistant vocal. Tu réponds toujours en français. \
		Ton objectif est de répondre le plus efficacement et de façon la plus concise possible \
		tout en conservant la complétude et l'exactitude du message.\
		Tu ne dois jamais commencer tes phrases par Jarvis mais il peut se trouver ailleurs dans la phrase au besoin"
	}
]
Jarvis_option = {}

translate_role = [
	{
		"role": "system",
		"content": "Tu reçois un message de reconnaissance vocale francophone, \
			traduis le en message comprehensible en français pour un LLM si tu detectes une incohérence dans la phrase \
			sinon, répètes le tel quel."
	},
	{}
]

def AI_translate_user_input(content : Queue, trad_lock : Lock, AI_lock : Lock, cancel : Event):
	print("AI_TRANSLATE")
	while True:
		if cancel.is_set():
			break
		if not trad_lock.locked():
			print("AI_TRANSLATE_GO")
			msg = content.get()
			print("msg : ",msg)
			if msg["content"] == "":
				continue
			print("msg = ",msg)
			translate_role[1] = {'role': 'user', 'content': msg["content"]}
			response = ollama.chat(
				model="gemma3",
				messages=translate_role
			)
			trad_lock.acquire()
			content.queue.clear()
			print("Trad : ", response.message)
			content.put(response.message)
			AI_lock.release()
			# return response.message

def Gemma3(content):
	if content == "":
		return
	print("content = ", content)
	Jarvis_history.append({'role': 'user', 'content': content})
	response = ollama.chat(
		model="gemma3",
		messages=Jarvis_history,
		options=Jarvis_option
	)
	Jarvis_history.append(response.message)
	return response

def AI_resume_msg(content : Queue, cancel : Event):
	print("AI_RESUME")
	while True:
		if (cancel.is_set()):
			break
		if (len(Jarvis_history) >= 5):
			resume = [{
				"role": "system",
				"content": "Ton objectif est de résumé les messages suivant le plus concisément possible,  \
					sans perdre la moindre information, sans aucune autre information à ajouter dans l'objectif de \
					les renvoyer à une IA pour que son historique soit moins lourd."
			}]
			for i in range(1, len(Jarvis_history)):
				resume.append(Jarvis_history[i])
			response = ollama.chat(
				model="gemma3",
				messages=resume
			)
			print(Jarvis_history)
			print(response.message)
			break

if __name__ == "__main__":
	Gemma3("Bonjour Jarvis, présente-toi en une phrase.")