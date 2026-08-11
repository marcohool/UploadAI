import argparse
import random
from dotenv import load_dotenv
from pathlib import Path
from services.instragram_integration import upload_photo
from services.openai_model import OpenAIModel
from services.flux_model import FluxModel
from utils.data_helpers import (
    format_exclusions,
    generate_caption,
    get_caption_angle,
    get_caption_shape,
    get_exclusions,
    get_fame_tier,
    get_framing,
    get_human_presence,
    get_medium_look,
    get_random_country,
    get_random_time_of_day,
    get_recent_caption_angles,
    get_recent_countries,
    get_shot_category,
    get_weather,
    handle_image_generation,
    load_config,
    load_history,
    load_prompts,
    save_history_entry,
    should_ask_question,
)
from utils.json_processing import process_dalle_prompt_request, process_location_candidates
from utils.prompt_cleanup import clean_image_prompt
import schedule
import time

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

config = load_config()
openAi = OpenAIModel(model=config['openai_model'])
flux = FluxModel(model=config['flux_model'], inputs=config.get('flux_inputs'))


prompts = load_prompts()


def main(dry_run=False):
    try:
        history = load_history()

        # Get random country to generate image of, damping down countries used
        # in the last handful of posts
        randomCountry = get_random_country(
            "data/countryList.txt", recent_countries=get_recent_countries(history))
        print("Got country -> ", randomCountry)

        # Sample the photographic parameters here rather than letting the model
        # choose them - left to itself it picks the same ones every time
        shotCategory = get_shot_category()
        fameTier = get_fame_tier()
        timeOfDay = get_random_time_of_day()
        weather = get_weather()
        framing = get_framing()
        mediumLook = get_medium_look()
        humanPresence = get_human_presence()

        # Same reasoning for the caption: what it says and how it sits on the
        # screen are both sampled, so consecutive posts don't share a template
        captionAngle = get_caption_angle(get_recent_caption_angles(history))
        captionShape = get_caption_shape()
        askQuestion = should_ask_question()

        print("Got shot category -> ", shotCategory)
        print("Got fame tier -> ", fameTier)
        print("Got time of day -> ", timeOfDay)
        print("Got weather -> ", weather)
        print("Got framing -> ", framing)
        print("Got medium look -> ", mediumLook)
        print("Got human presence -> ", humanPresence)
        print("Got caption angle -> ", captionAngle)
        print("Got caption shape -> ", captionShape)
        print("Got caption question -> ", askQuestion)

        # Stage 1: ask for a spread of candidate subjects and pick one at
        # random. Asking for a single subject just returns the country's most
        # obvious landmark almost every time.
        used_locations, recent_subjects = get_exclusions(history, randomCountry)
        candidates_json = openAi.get_text_response(1.2, prompts['location_candidates_prompt'].format(
            randomCountry=randomCountry, shotCategory=shotCategory, fameTier=fameTier,
            exclusions=format_exclusions(used_locations, recent_subjects)))

        candidates = process_location_candidates(candidates_json)
        candidate = random.choice(candidates)
        print(f"Picked 1 of {len(candidates)} candidates -> ", candidate)

        # Stage 2: describe that exact photograph
        image_prompt_json = openAi.get_text_response(1.0, prompts['image_prompt_template'].format(
            chosenLocation=candidate['location'], subject=candidate['subject'],
            shotCategory=shotCategory, timeOfDay=timeOfDay, weather=weather,
            framing=framing, mediumLook=mediumLook, humanPresence=humanPresence))

        chosen_location, image_prompt = process_dalle_prompt_request(
            image_prompt_json)

        # Strip filler adjectives and any editorial closing sentence the model
        # added, and keep the prompt inside the image model's text budget
        image_prompt = clean_image_prompt(image_prompt)
        print("Got prompt -> ", image_prompt)

        # Generate image
        handle_image_generation(flux, image_prompt, "assets/generatedImage.jpg")

        # The caption is written from the place itself, not from the image
        # prompt - describing the photo to somebody already looking at it is
        # what made every caption interchangeable
        caption = generate_caption(openAi, prompts,
                                   location=chosen_location, country=randomCountry,
                                   subject=candidate['subject'], shot_category=shotCategory,
                                   angle=captionAngle, shape=captionShape,
                                   ask_question=askQuestion)

        if dry_run:
            print("Dry run: skipping Instagram upload and history write.")
            print(f"Location -> {chosen_location}, {randomCountry}")
            print(f"Caption -> {caption}")
            return

        # Upload photo. chosen_location already ends with the country, so it's
        # used as-is, with the bare country as a fallback for obscure places
        # Instagram has never heard of.
        upload_photo("assets/generatedImage.jpg", caption,
                     chosen_location, randomCountry)

        # Only record the post once it's actually live, so a failed run doesn't
        # burn a location
        save_history_entry({
            "country": randomCountry,
            "location": candidate['location'],
            "subject": candidate['subject'],
            "shot_category": shotCategory,
            "caption_angle": captionAngle,
        })

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
        # Tuesday
        schedule.every().tuesday.at("19:00").do(main)

        # Wednesday
        schedule.every().wednesday.at("19:00").do(main)

        # Thursday
        schedule.every().thursday.at("19:00").do(main)

        # Sunday
        schedule.every().sunday.at("19:00").do(main)

        while True:
            schedule.run_pending()
            time.sleep(1)
