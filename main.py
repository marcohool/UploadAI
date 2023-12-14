import os
import urllib.request
from openai import OpenAI
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.types import Location
from pathlib import Path
from PIL import Image
import random
from geopy.geocoders import Nominatim


dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

client = OpenAI(
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


def uploadPhoto(image1Path, caption, country):
    cl = Client()
    cl.login(os.getenv('IG_UNAME'), os.getenv('IG_PWD'))

    # Get location of country
    geolocator = Nominatim(user_agent="get_lat_lng")
    location = geolocator.geocode(country)

    if location:
        lat_lng = [location.latitude, location.longitude]
    else:
        lat_lng = []

    print(f"Lat_lng = {lat_lng}")

    cl.photo_upload(
        path=image1Path,
        caption=caption,
        location=Location(name=country, lat=lat_lng[0], lng=lat_lng[1])
    )


def getCountry(fileName):
    with open(fileName, 'r') as file:
        lines = file.readlines()

        random_number = random.randint(0, len(lines)-1)

        return lines[random_number]


def main():
    randomCountry = getCountry("countryList.txt")

    dallePrompt = getTextResponse(client, 1, f"Design a prompt for DALL-E 3 to produce an attention-grabbing realistic image of the beauty of {randomCountry} using a 35mm lens. Please include specific details such as the desired setting, objects, colors, mood, and unique elements to be incorporated. Additionally, consider the mood and atmosphere you want to convey, and provide descriptive adjectives to guide the image creation. Specify the desired perspective and composition, as well as the preferred lighting and time of day. If applicable, indicate any desired action or movement within the image. Aim for a balance between providing sufficient detail and conciseness in your prompt. Feel free to employ analogies or comparisons to further clarify your vision. Lastly, indicate any desired styles or themes, and outline an iterative approach for refining the image. Return nothing but this prompt, no other text.")
    print("\nDalle prompt generated -> ", dallePrompt)

    # Generate image
    generatedImageLink = getImageResponse(client, dallePrompt)
    print("\nImage generated -> ", generatedImageLink)

    # Download image
    urllib.request.urlretrieve(generatedImageLink, "dalleImage.jpg")

    # Get photo caption
    caption = getTextResponse(
        client, 1, f"Generate a 1 or 2 sentence caption for this image description - describing it briefly. After that include two new lines and list a total of 10-15 hashtags for social media. Please reply with this caption and nothing else \n'{dallePrompt}'")
    print("Caption prompt generated -> ", caption)

    uploadPhoto("dalleImage.jpg", caption, randomCountry)


if __name__ == "__main__":
    main()
