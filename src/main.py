import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from services.instragram_integration import upload_photo
from services.openai_generation import get_text_response
from utils.data_helpers import get_random_country, handle_image_generation
from utils.json_processing import process_dalle_prompt_request
import schedule
import time

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

client = OpenAI(
    api_key=os.getenv('OPENAI_KEY'),
)


def main():
    try:
        # Get random country to generate image of
        randomCountry = get_random_country("data/countryList.txt")
        print("Got country -> ", randomCountry)

        # Get prompt to use for image generation
        dallePromptJSON = get_text_response(client, "gpt-4-1106-preview", 1, f"Design a prompt for DALL-E 3 to produce an attention-grabbing realistic and beatiful image of the beauty of {randomCountry}. Pick a place in {randomCountry} with a name and base your image there, try to stay away from beaches at sunset/sunrise. Please include specific details such as the desired setting, objects, colors, mood, and unique elements to be incorporated. Additionally, consider the mood and atmosphere you want to convey, and provide descriptive adjectives to guide the image creation. Specify the desired perspective and composition, as well as the preferred lighting and time of day. If applicable, indicate any desired action or movement within the image. Aim for a balance between providing sufficient detail and conciseness in your prompt. Feel free to employ analogies or comparisons to further clarify your vision. Lastly, indicate any desired styles or themes, and outline an iterative approach for refining the image. Return nothing but this prompt, no other text. The first word of your response should contain just the name of the place you are drawing as a location (town, city) within {randomCountry}, nothing else. Respond in a json format, with the first field 'chosenLocation' and second 'promptValue'")
        chosen_location, dalle_prompt = process_dalle_prompt_request(
            dallePromptJSON)

        # Generate image
        caption = handle_image_generation(
            client, dalle_prompt, "assets/dalleImage.jpg", True)

        # Upload photo
        upload_photo("assets/dalleImage.jpg", caption,
                     f"{randomCountry}")

    except Exception as e:
        print("Couldn't perform main: ", e)


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
