import os
import urllib.request
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image
# from text_generator import getTextResponse
# from image_generator import getImageResponse


dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv('OPENAI_KEY'),
)


def getTextResponse(client, temperature, inputText):
    chat_completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=temperature,
        messages=[
            {
                "role": "user",
                "content": inputText,
            }
        ],
    )
    print("??")

    return chat_completion.choices[0].message.content


def getImageResponse(client, inputText):
    response = client.images.generate(
        model="dall-e-3",
        prompt=inputText,
        size="1024x1024",
        quality="hd",
        n=1,
    )

    return response.data[0].url


def main():
    dallePrompt = getTextResponse(client, 1, "Design a prompt for DALL-E 3 to produce an attention-grabbing image tailored for social media. Please include specific details such as the desired setting, objects, colors, mood, and unique elements to be incorporated. Additionally, consider the mood and atmosphere you want to convey, and provide descriptive adjectives to guide the image creation. Specify the desired perspective and composition, as well as the preferred lighting and time of day. If applicable, indicate any desired action or movement within the image. Aim for a balance between providing sufficient detail and conciseness in your prompt. Feel free to employ analogies or comparisons to further clarify your vision. Lastly, indicate any desired styles or themes, and outline an iterative approach for refining the image. Return nothing but this prompt, no other text.")
    print("\nDalle prompt generated -> ", dallePrompt)

    generatedImageLink = getImageResponse(client, dallePrompt)
    print("\nImage generated -> ", generatedImageLink)

    urllib.request.urlretrieve(generatedImageLink, "dalleImage.png")

    img = Image.open(r"dalleImage.png")
    img.show()


if __name__ == "__main__":
    main()
