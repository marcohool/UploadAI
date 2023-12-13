
chat_completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    temperature=0.8,
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
)
print(chat_completion.choices[0].message)
