import os
import urllib.request
from openai import OpenAI
from dotenv import load_dotenv
from instagrapi.types import Location
from instagrapi import Client
from pathlib import Path
from PIL import Image
import schedule
import random
import time
from geopy.geocoders import Nominatim


dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

client = OpenAI(
    api_key=os.getenv('OPENAI_KEY'),
)


def getTextResponse(client, temperature, inputText):
    chat_completion = client.chat.completions.create(
        model="gpt-4",
        temperature=temperature,
        messages=[
            {
                "role": "user",
                "content": inputText,
            }
        ],
    )

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


def uploadPhoto(image1Path, caption, locationName):
    cl = Client()
    cl.login(os.getenv('IG_UNAME'), os.getenv('IG_PWD'))

    # Get location of country
    geolocator = Nominatim(user_agent="get_lat_lng")
    location = geolocator.geocode(locationName)

    if location:
        lat_lng = [location.latitude, location.longitude]
        cl.photo_upload(
            path=image1Path,
            caption=caption,
            location=Location(name=locationName,
                              lat=lat_lng[0], lng=lat_lng[1])
        )
    else:
        cl.photo_upload(
            path=image1Path,
            caption=caption
        )

    print(f"Location = {location}")


def getCountry(fileName):
    with open(fileName, 'r') as file:
        lines = file.readlines()

        random_number = random.randint(0, len(lines)-1)

        return lines[random_number]


def main():
    randomCountry = getCountry("data/countryList.txt")
    print("Got country -> ", randomCountry)

    dallePrompt = getTextResponse(client, 1, f"Design a prompt for DALL-E 3 to produce an attention-grabbing realistic image of the beauty of {randomCountry}. Pick a place in {randomCountry} with a name and base your image there. Please include specific details such as the desired setting, objects, colors, mood, and unique elements to be incorporated. Additionally, consider the mood and atmosphere you want to convey, and provide descriptive adjectives to guide the image creation. Specify the desired perspective and composition, as well as the preferred lighting and time of day. If applicable, indicate any desired action or movement within the image. Aim for a balance between providing sufficient detail and conciseness in your prompt. Feel free to employ analogies or comparisons to further clarify your vision. Lastly, indicate any desired styles or themes, and outline an iterative approach for refining the image. Return nothing but this prompt, no other text. The first word of your response should contain just the name of the place you are drawing as a location (town, city) within {randomCountry}, nothing else.")

    # The first sentence is the first element of the 'sentences' list
    locationGenerted = dallePrompt.split(" ")[0]
    print("Location generated -> ", locationGenerted)

    # The rest of the content is the remaining sentences joined back together
    print("\nDalle prompt generated -> ", dallePrompt)

    # Generate image
    generatedImageLink = getImageResponse(client, dallePrompt)
    print("\nImage generated -> ", generatedImageLink)

    # Download image
    urllib.request.urlretrieve(generatedImageLink, "assets/dalleImage.jpg")

    # Get photo caption
    caption = getTextResponse(
        client, 1, f"Generate a 1 or 2 sentence caption for this image description, describing it briefly, along with a list of total 10-15 hashtags for social media use. Please reply with this caption and nothing else: '{dallePrompt}'")

    # Add space between hashtags and caption
    hash_index = caption.find('#')
    if hash_index != -1:
        caption = caption[:hash_index] + "\n" + caption[hash_index:]

    print("Caption prompt generated -> ", caption)

    uploadPhoto("assets/dalleImage.jpg", caption,
                f"{locationGenerted}, {randomCountry}")


if __name__ == "__main__":
    schedule.every().day.at("07:00").do(main)
    schedule.every().day.at("19:00").do(main)
    schedule.every().day.at("00:00").do(main)

    while True:
        schedule.run_pending()
        time.sleep(1)
