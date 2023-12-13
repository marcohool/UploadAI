from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import os

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv('OPENAI_KEY'),
)



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
