import os
from openai import BadRequestError, OpenAI


class OpenAIModel:
    def __init__(self, model="gpt-4o", reasoning_effort=None):
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_KEY'),
        )
        self.model = model
        # Reasoning tokens are hidden but billed as output, and they were most
        # of the bill on gpt-5.5. None leaves the model's own default.
        self.reasoning_effort = reasoning_effort
        self.supports_temperature = True

    def get_text_response(self, temperature, inputText):
        request = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": inputText,
                }
            ],
        }

        if self.supports_temperature:
            request["temperature"] = temperature

        if self.reasoning_effort:
            request["reasoning_effort"] = self.reasoning_effort

        try:
            chat_completion = self.client.chat.completions.create(**request)
        except BadRequestError as e:
            # Reasoning models only accept the default temperature. The
            # variety the temperature was there for comes from the sampling in
            # data_helpers anyway, so drop it rather than lose the post.
            if "temperature" not in str(e) or "temperature" not in request:
                raise

            print(f"{self.model} rejected temperature={temperature} - "
                  f"retrying with the default")
            self.supports_temperature = False
            del request["temperature"]
            chat_completion = self.client.chat.completions.create(**request)

        return chat_completion.choices[0].message.content
