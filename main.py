from openai import OpenAI


client = OpenAI(
    # This is the default and can be omitted
    api_key="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",
)

# chat_completion = client.chat.completions.create(
#     model="gpt-3.5-turbo",
#     temperature=0.8,
#     messages=[
#         {
#             "role": "user",
#             "content": "Say this is a test",
#         }
#     ],
# )
# print(chat_completion.choices[0].message)

response = client.images.generate(
    model="dall-e-3",
    prompt="a white siamese cat",
    size="1024x1024",
    quality="hd",
    n=1,
)

image_url = response.data[0].url

print(response)

print(image_url)


def main():
    pass


if __name__ == "__main__":
    main()
