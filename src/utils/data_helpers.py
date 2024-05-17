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


def get_random_country(fileName):
    with open(fileName, 'r') as file:
        lines = file.readlines()

        random_number = random.randint(0, len(lines)-1)

        return lines[random_number]


def load_prompts(config_file="data/prompts.json"):
    with open(config_file, 'r') as f:
        return json.load(f)


def handle_image_generation(model, prompt, imageFileName, caption):
    generatedImageLink = model.get_image_response(prompt)
    print("\nImage generated -> ", generatedImageLink)

    # Download image
    urllib.request.urlretrieve(
        generatedImageLink, imageFileName)

    if caption:
        # Get photo caption
        caption = model.get_text_response(1,
                                          load_prompts()['caption_prompt'].format(prompt=prompt))

        # Add space between hashtags and caption
        caption = caption.replace('"', '')
        hash_index = caption.find('#')
        if hash_index != -1:
            caption = '"' + caption[:hash_index].strip() + \
                '"' + '\n\n\n' + caption[hash_index:]

        print("Caption prompt generated -> ", caption)

        return caption
