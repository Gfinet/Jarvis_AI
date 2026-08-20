import ollama
from threading import Thread, Lock, Event
from queue import Queue


def AI_resume_msg(content):
	print("AI_RESUME")
	while content == "":
		continue
	response = ollama.chat(
		model="gemma3",
		messages=[
			{
			"role": "system",
			"content": "Ton objectif est de résumé les messages suivant le plus court possible et \
				sans perdre la moindre information"
			},
			{
				"role": "user",
				"content": content,
			}
		]
	)
	return response.message

def AI_translate_user_input(content : Queue, trad_lock : Lock, voice_lock : Lock, cancel : Event):
	print("AI_TRANSLATE")
	while True:
		if cancel.is_set():
			break
		if not trad_lock.locked():
			print("AI_TRANSLATE_GO")
			msg = content.get()
			if msg == "":
				continue
			print("msg = ",msg)
			response = ollama.chat(
				model="gemma3",
				messages=[
					{
						"role": "system",
						"content": "Tu reçois un message de reconnaissance vocale francophone \
							traduis le en message comprehensible français pour un LLM si tu detectes une incohérence dans la phrase \
							sinon, laisse le tel quel"
					},
					{
						"role": "user",
						"content": msg,
					}
				]
			)
			trad_lock.acquire()
			content.queue.clear()
			print("Trad : ", response.message.content)
			content.put(response.message.content)
			voice_lock.release()
			# return response.message

def Gemma3(content):
	if content == "":
		return
	print("content = ", content)
	response = ollama.chat(
		model="gemma3",
		messages=[
			{
			"role": "system",
			"content": "Tu es Jarvis, un assistant vocal. Tu réponds toujours en français. \
				Ton objectif est de répondre le plus efficacement et de façon la plus concise possible \
				tout en conservant la complétude et l'exactitude du message."
			},
			{
				"role": "user",
				"content": content,
			}
		],
		options={

			
		}
	)
	return response

if __name__ == "__main__":
	Gemma3("Bonjour Jarvis, présente-toi en une phrase.")