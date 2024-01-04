import random
import urllib.request
from services.openai_generation import get_image_response, get_text_response


def get_random_country(fileName):
    with open(fileName, 'r') as file:
        lines = file.readlines()

        random_number = random.randint(0, len(lines)-1)

        return lines[random_number]


def handle_image_generation(client, dalle_prompt, imageFileName, caption):
    generatedImageLink = get_image_response(client, dalle_prompt)
    print("\nImage generated -> ", generatedImageLink)

    # Download image
    urllib.request.urlretrieve(
        generatedImageLink, imageFileName)

    if caption:
        # Get photo caption
        caption = get_text_response(
            client, "gpt-4-1106-preview", 1, f"Generate a 1 or 2 sentence caption for this image description, describing it briefly, along with a list of total 20 hashtags for social media use. Please reply with this caption and nothing else: '{dalle_prompt}'")

        # Add space between hashtags and caption
        caption = caption.replace('"', '')
        hash_index = caption.find('#')
        if hash_index != -1:
            caption = '"' + caption[:hash_index].strip() + \
                '"' + '\n\n\n' + caption[hash_index:]

        print("Caption prompt generated -> ", caption)

        return caption
