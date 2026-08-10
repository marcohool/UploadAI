import os
import random
import urllib.request
import json


def get_random_time_of_day():
    times_of_day = ['sunrise', 'morning', 'afternoon', 'sunset', 'night']
    return random.choice(times_of_day)


def get_photographic_style():
    photographic_style = [
        "Landscape",
        "Urban Exploration (Urbex)",
        "Street Photography",
        "Architectural Photography",
        "Aerial Photography",
        "Night Photography",
        "Black and White",
        "Panoramic",
        "HDR (High Dynamic Range)",
        "Minimalist",
        "Macro",
        "Documentary",
        "Cinematic",
        "Long Exposure",
        "Travel Photography",
        "Environmental Portraiture",
        "Surreal",
        "Vintage/Retro",
        "Tilt-Shift",
        "Infrared"
    ]
    return random.choice(photographic_style)


def get_shot_category():
    shot_categories = [
        "Iconic Landmarks & Cityscape",
        "Urban Street Life",
        "Small Town/Village",
        "Nature & Landscape",
        "Mountains",
        "Beach & Coast",
        "Wildlife & Animals",
        "Countryside/Rural Life",
        "Cultural & Historical Sites",
        "Local Food & Markets",
        "People & Everyday Culture"
    ]
    return random.choice(shot_categories)


POPULAR_COUNTRIES = {
    "United States", "United Kingdom", "France", "Italy", "Spain", "Germany",
    "Greece", "Portugal", "Netherlands", "Switzerland", "Austria", "Ireland",
    "Iceland", "Norway", "Sweden", "Denmark", "Japan", "China", "India",
    "Thailand", "Vietnam", "Indonesia", "South Korea", "Australia",
    "New Zealand", "Canada", "Mexico", "Brazil", "Argentina", "Peru",
    "Egypt", "Morocco", "South Africa", "Turkey", "United Arab Emirates",
    "Croatia",
}

POPULAR_COUNTRY_WEIGHT = 5


def get_random_country(fileName):
    with open(fileName, 'r') as file:
        countries = [line.strip() for line in file if line.strip()]

    weights = [POPULAR_COUNTRY_WEIGHT if country in POPULAR_COUNTRIES else 1
               for country in countries]

    return random.choices(countries, weights=weights, k=1)[0]


def load_prompts(config_file="data/prompts.json"):
    with open(config_file, 'r') as f:
        return json.load(f)


def load_config(config_file="data/config.json"):
    with open(config_file, 'r') as f:
        return json.load(f)


def handle_image_generation(text_model, image_model, prompts, prompt, imageFileName, caption):
    generatedImageLink = image_model.generate_image(prompt)
    print("\nImage generated -> ", generatedImageLink)

    # Download image
    os.makedirs(os.path.dirname(imageFileName) or ".", exist_ok=True)
    urllib.request.urlretrieve(
        generatedImageLink, imageFileName)

    if caption:
        # Get photo caption
        caption = text_model.get_text_response(1,
                                               prompts['caption_prompt'].format(prompt=prompt))

        # Add space between hashtags and caption
        caption = caption.replace('"', '')
        hash_index = caption.find('#')
        if hash_index != -1:
            caption = '"' + caption[:hash_index].strip() + \
                '"' + '\n\n\n' + caption[hash_index:]

        print("Caption prompt generated -> ", caption)

        return caption
