import argparse
import json
from dotenv import load_dotenv
from pathlib import Path
from services.instragram_integration import upload_photo
from services.openai_model import OpenAIModel
from services.flux_model import FluxModel
from utils.geo import geocode
from utils.data_helpers import (
    alt_text,
    format_exclusions,
    generate_caption,
    get_caption_angle,
    get_caption_shape,
    get_exclusions,
    get_fame_tier,
    get_framing_options,
    get_human_presence,
    get_light_options,
    get_medium_look,
    get_random_country,
    get_recent_caption_angles,
    get_recent_countries,
    get_shot_category,
    handle_image_generation,
    is_landmark_tier,
    load_config,
    load_history,
    load_prompts,
    pick_candidate,
    save_history_entry,
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

# World-famous wonders go to a second model when one is configured. In blind
# tests FLUX 3's grounding (it looks the place up before drawing) won on
# accuracy 23 times out of 28 - FLUX.2 drew Kronborg as a red-brick castle and
# Victoria Falls as a horseshoe - but FLUX.2 won on scroll-stopping appeal by
# the same margin. Accuracy matters most where viewers know what the place
# really looks like, so that's where the grounded model is used.
landmark_flux = (FluxModel(model=config['landmark_flux_model'],
                           inputs=config.get('landmark_flux_inputs'))
                 if config.get('landmark_flux_model') else flux)


prompts = load_prompts()


def main(dry_run=False, image_path="assets/generatedImage.jpg"):
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
        lightOptions = get_light_options()
        framingOptions = get_framing_options()
        mediumLook = get_medium_look()
        humanPresence = get_human_presence()

        # Same reasoning for the caption: what it says and how it sits on the
        # screen are both sampled, so consecutive posts don't share a template
        captionAngle = get_caption_angle(get_recent_caption_angles(history))
        captionShape = get_caption_shape()

        print("Got shot category -> ", shotCategory)
        print("Got fame tier -> ", fameTier)
        print("Got light options -> ", lightOptions)
        print("Got framing options -> ", framingOptions)
        print("Got medium look -> ", mediumLook)
        print("Got human presence -> ", humanPresence)
        print("Got caption angle -> ", captionAngle)
        print("Got caption shape -> ", captionShape)

        # Stage 1: ask for a spread of candidate subjects and pick one of the
        # strongest. Asking for a single subject just returns the country's
        # most obvious landmark almost every time.
        used_locations, recent_subjects = get_exclusions(history, randomCountry)
        candidates_json = openAi.get_text_response(1.2, prompts['location_candidates_prompt'].format(
            randomCountry=randomCountry, shotCategory=shotCategory, fameTier=fameTier,
            exclusions=format_exclusions(used_locations, recent_subjects)))

        candidates = process_location_candidates(candidates_json)
        candidate = pick_candidate(
            candidates, exists=lambda location: geocode(location) is not None,
            used_locations=used_locations)
        print(f"Picked 1 of {len(candidates)} candidates -> ", candidate)

        # Stage 2: describe that exact photograph
        image_prompt_json = openAi.get_text_response(1.0, prompts['image_prompt_template'].format(
            chosenLocation=candidate['location'], subject=candidate['subject'],
            whySpectacular=candidate['why_spectacular'], shotCategory=shotCategory,
            lightOptions="\n".join(f"- {option}" for option in lightOptions),
            framingOptions="\n".join(f"- {option}" for option in framingOptions),
            mediumLook=mediumLook, humanPresence=humanPresence))

        chosen_location, image_prompt, light_condition, framing = process_dalle_prompt_request(
            image_prompt_json)
        print("Got light condition -> ", light_condition)
        print("Got framing -> ", framing)

        # Strip filler adjectives and any editorial closing sentence the model
        # added, and keep the prompt inside the image model's text budget
        image_prompt = clean_image_prompt(image_prompt)
        print("Got prompt -> ", image_prompt)

        # Generate image
        image_model = landmark_flux if is_landmark_tier(fameTier) else flux
        print("Got image model -> ", image_model.model)
        handle_image_generation(image_model, image_prompt, image_path)

        # The caption is written from the place itself, not from the image
        # prompt - describing the photo to somebody already looking at it is
        # what made every caption interchangeable
        caption = generate_caption(openAi, prompts,
                                   location=chosen_location, country=randomCountry,
                                   subject=candidate['subject'], shot_category=shotCategory,
                                   angle=captionAngle, shape=captionShape)

        if dry_run:
            print("Dry run: skipping Instagram upload and history write.")
            print(f"Location -> {chosen_location}, {randomCountry}")
            print(f"Caption -> {caption}")

            # Everything that went into the post, next to the image, so a batch
            # of dry runs can be compared without digging through logs
            with open(Path(image_path).with_suffix(".json"), "w") as f:
                json.dump({
                    "country": randomCountry, "location": chosen_location,
                    "candidate": candidate, "shot_category": shotCategory,
                    "fame_tier": fameTier, "image_model": image_model.model,
                    "light_condition": light_condition,
                    "framing": framing, "medium_look": mediumLook,
                    "human_presence": humanPresence, "caption_angle": captionAngle,
                    "caption_shape": captionShape, "image_prompt": image_prompt,
                    "caption": caption,
                }, f, indent=2, ensure_ascii=False)
            return

        # Upload photo. chosen_location already ends with the country, so it's
        # used as-is, with the bare country as a fallback for obscure places
        # Instagram has never heard of.
        upload_photo(image_path, caption,
                     chosen_location, randomCountry,
                     alt_text=alt_text(candidate['subject'], chosen_location, randomCountry))

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
    parser.add_argument("--output", default="assets/generatedImage.jpg",
                        help="Where to write the image in a dry run (a .json of the post lands beside it)")
    args = parser.parse_args()

    if args.dry_run:
        main(dry_run=True, image_path=args.output)
    else:
        # Tuesday
        schedule.every().tuesday.at("18:00").do(main)

        # Wednesday
        schedule.every().wednesday.at("18:00").do(main)

        # Thursday
        schedule.every().thursday.at("18:00").do(main)

        # Sunday
        schedule.every().sunday.at("18:00").do(main)

        while True:
            schedule.run_pending()
            time.sleep(1)
