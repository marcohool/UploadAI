
def get_text_response(client, model, temperature, inputText):
    chat_completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {
                "role": "user",
                "content": inputText,
            }
        ],
    )

    return chat_completion.choices[0].message.content


def get_image_response(client, inputText):
    response = client.images.generate(
        model="dall-e-3",
        prompt=inputText,
        size="1024x1024",
        quality="hd",
        n=1,
    )

    return response.data[0].url
