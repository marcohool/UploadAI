import argparse
from dotenv import load_dotenv
from pathlib import Path
from services.instragram_integration import upload_photo
from services.openai_model import OpenAIModel
from services.flux_model import FluxModel
from utils.data_helpers import get_photographic_style, get_random_country, get_shot_category, handle_image_generation, get_random_time_of_day, load_prompts
from utils.json_processing import process_dalle_prompt_request
import schedule
import time

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

openAi = OpenAIModel()
flux = FluxModel()


prompts = load_prompts()


def main(dry_run=False):
    try:
        # Get random country to generate image of
        randomCountry = get_random_country("data/countryList.txt")
        print("Got country -> ", randomCountry)

        # Get random time of day for image to be generated in
        timeOfDay = get_random_time_of_day()
        print("Got time of day -> ", timeOfDay)

        # Get photographic style
        photographicStyle = get_photographic_style()
        print("Got photographic style -> ", photographicStyle)

        # Get shot category (what the image actually depicts)
        shotCategory = get_shot_category()
        print("Got shot category -> ", shotCategory)

        # Get prompt to use for image generation
        image_prompt_json = openAi.get_text_response(1.2, prompts['image_prompt_template'].format(
            randomCountry=randomCountry, timeOfDay=timeOfDay, photographicStyle=photographicStyle,
            shotCategory=shotCategory))

        print("Got prompt -> ", image_prompt_json)
        chosen_location, image_prompt = process_dalle_prompt_request(
            image_prompt_json)

        # Generate image
        caption = handle_image_generation(openAi, flux, prompts,
                                          image_prompt, "assets/generatedImage.jpg", True)

        if dry_run:
            print("Dry run: skipping Instagram upload.")
            print(f"Location -> {chosen_location}, {randomCountry}")
            print(f"Caption -> {caption}")
            return

        # Upload photo
        upload_photo("assets/generatedImage.jpg", caption,
                     f"{chosen_location}, {randomCountry}")

    except Exception as e:
        print("Couldn't perform main: ", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate an image and caption without uploading to Instagram")
    args = parser.parse_args()

    if args.dry_run:
        main(dry_run=True)
    else:
        # Monday
        schedule.every().monday.at("09:00").do(main)
        schedule.every().monday.at("17:00").do(main)

        # Tuesday
        schedule.every().tuesday.at("09:00").do(main)
        schedule.every().tuesday.at("17:00").do(main)

        # Wednesday
        schedule.every().wednesday.at("05:00").do(main)
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
