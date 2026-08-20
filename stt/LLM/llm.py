import ollama



def Gemma3(content):
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