import os
from openai import OpenAI


class OpenAIModel:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_KEY'),
        )
        self.model = "gpt-4o"

    def get_text_response(self, temperature, inputText):
        chat_completion = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "content": inputText,
                }
            ],
        )

        return chat_completion.choices[0].message.content

    def get_image_response(self, inputText):
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=inputText,
            size="1024x1024",
            quality="hd",
            n=1,
        )

        return response.data[0].url
