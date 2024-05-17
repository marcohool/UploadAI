import random
import urllib.request
from main import prompts


def get_random_time_of_day():
    times_of_day = ['sunrise', 'morning', 'afternoon', 'sunset', 'night']
    return random.choice(times_of_day)


def get_random_country(fileName):
    with open(fileName, 'r') as file:
        lines = file.readlines()

        random_number = random.randint(0, len(lines)-1)

        return lines[random_number]


def handle_image_generation(model, prompt, imageFileName, caption):
    generatedImageLink = model.get_image_response(model, 1, prompt)
    print("\nImage generated -> ", generatedImageLink)

    # Download image
    urllib.request.urlretrieve(
        generatedImageLink, imageFileName)

    if caption:
        # Get photo caption
        caption = model.get_text_response(1,
                                          prompts['caption_prompt'].format(prompt=prompt))

        # Add space between hashtags and caption
        caption = caption.replace('"', '')
        hash_index = caption.find('#')
        if hash_index != -1:
            caption = '"' + caption[:hash_index].strip() + \
                '"' + '\n\n\n' + caption[hash_index:]

        print("Caption prompt generated -> ", caption)

        return caption
