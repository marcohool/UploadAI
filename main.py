import os
import urllib.request
from openai import OpenAI
from dotenv import load_dotenv
from instagrapi.types import Location
from instagrapi.exceptions import LoginRequired
from instagrapi import Client
from pathlib import Path
import schedule
import logging
import time
import random
from geopy.geocoders import Nominatim
import json

logger = logging.getLogger()

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

client = OpenAI(
    api_key=os.getenv('OPENAI_KEY'),
)


def loginUser():
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """
    cl = Client()
    session = cl.load_settings("data/session.json")

    if session:
        try:
            cl.set_settings(session)
            cl.login(os.getenv('IG_UNAME'), os.getenv('IG_PWD'))

            # Check if session is valid
            try:
                cl.get_timeline_feed()
            except LoginRequired:
                logger.info(
                    "Session invalid -> logging in with username and password")

                old_session = cl.get_settings()

                # Use the same device UUID
                cl.set_settings({})
                cl.set_settings(old_session["uuids"])

                cl.login(os.getenv('IG_UNAME'), os.getenv('IG_PWD'))

            cl.dump_settings("data/session.json")
            return cl
        except Exception as e:
            logger.info("Couldn't login user using session information: ", e)

    try:
        logger.info(
            f"Attempting to login with username and password\n\tUsername: {os.getenv('IG_UNAME')}")
        if cl.login(os.getenv('IG_UNAME'), os.getenv('IG_PWD')):
            cl.dump_settings("data/session.json")
            return cl
    except Exception as e:
        logger.info("Couldn't login user with username and password: ", e)

    raise Exception("Couldn't login user with either password or session")


def getTextResponse(client, model, temperature, inputText):
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
    cl = loginUser()

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

    dallePrompt = getTextResponse(client, "gpt-4-1106-preview", 1, f"Design a prompt for DALL-E 3 to produce an attention-grabbing realistic image of the beauty of {randomCountry}. Pick a place in {randomCountry} with a name and base your image there. Please include specific details such as the desired setting, objects, colors, mood, and unique elements to be incorporated. Additionally, consider the mood and atmosphere you want to convey, and provide descriptive adjectives to guide the image creation. Specify the desired perspective and composition, as well as the preferred lighting and time of day. If applicable, indicate any desired action or movement within the image. Aim for a balance between providing sufficient detail and conciseness in your prompt. Feel free to employ analogies or comparisons to further clarify your vision. Lastly, indicate any desired styles or themes, and outline an iterative approach for refining the image. Return nothing but this prompt, no other text. The first word of your response should contain just the name of the place you are drawing as a location (town, city) within {randomCountry}, nothing else. Respond in a json format, with the first field 'chosenLocation' and second 'promptValue'")
    print("\nDalle JSON response -> ", dallePrompt)

    # Parse JSON response
    try:
        dallePromptJson = dallePrompt.strip(
            '```json').replace("\n", "").replace("```", "")
        print("\nDalle prompt to JSON -> ", dallePromptJson)
        print("\nLoading JSON now\n")
        jsonPrompt = json.loads(dallePromptJson)

        locationGenerted = jsonPrompt["chosenLocation"]
        dallePrompt = jsonPrompt["promptValue"]

        print("\nDalle location generated -> ", locationGenerted)
        print("\nDalle prompt generated -> ", dallePrompt)

        # Generate image
        generatedImageLink = getImageResponse(client, dallePrompt)
        print("\nImage generated -> ", generatedImageLink)

        # Download image
        urllib.request.urlretrieve(generatedImageLink, "assets/dalleImage.jpg")

        # Get photo caption
        caption = getTextResponse(
            client, "gpt-4-1106-preview", 1, f"Generate a 1 or 2 sentence caption for this image description, describing it briefly, along with a list of total 20 hashtags for social media use. Please reply with this caption and nothing else: '{dallePrompt}'")

        # Add space between hashtags and caption
        hash_index = caption.find('#')
        if hash_index != -1:
            hash_index -= 1
            caption = '"' + caption[:hash_index] + \
                '"\n\n' + caption[hash_index:]

        print("Caption prompt generated -> ", caption)

        uploadPhoto("assets/dalleImage.jpg", caption,
                    f"{locationGenerted}, {randomCountry}")

    except Exception as e:
        logger.error("Couldn't perform main: ", e)


if __name__ == "__main__":
    # Monday
    schedule.every().monday.at("09:00").do(main)
    schedule.every().monday.at("17:00").do(main)

    # Tuesday
    schedule.every().tuesday.at("09:00").do(main)
    schedule.every().tuesday.at("17:00").do(main)

    # Wednesday
    schedule.every().wednesday.at("05:00").do(main)
    schedule.every().wednesday.at("11:00").do(main)
    schedule.every().wednesday.at("17:00").do(main)

    # Thursday
    schedule.every().thursday.at("12:00").do(main)
    schedule.every().thursday.at("18:00").do(main)

    # Friday
    schedule.every().friday.at("09:00").do(main)
    schedule.every().friday.at("17:00").do(main)

    # Saturday
    schedule.every().saturday.at("10:00").do(main)

    # Sunday
    schedule.every().sunday.at("09:00").do(main)
    schedule.every().sunday.at("18:00").do(main)

    while True:
        schedule.run_pending()
        time.sleep(1)
