import os
import random
import urllib.request
import json
from datetime import datetime, timezone


# Every axis below is sampled here in Python rather than left to the language
# model. Asked to choose freely, the model returns its favourite answer almost
# every time (35mm, golden hour, the most famous landmark), which is what makes
# a feed look repetitive. Sampling here forces genuine spread.


def get_random_time_of_day():
    times_of_day = [
        'pre-dawn blue hour, before the sun is up',
        'sunrise, with the sun still low and raking',
        'early morning, soft and cool',
        'mid-morning, bright and ordinary',
        'harsh midday sun, short hard shadows',
        'flat overcast afternoon light',
        'late afternoon, long shadows',
        'golden hour, warm low sun',
        'sunset',
        'dusk, blue hour after the sun has gone',
        'night, lit only by available artificial light',
        'late night, quiet and mostly dark',
    ]
    return random.choice(times_of_day)


def get_weather():
    weather = [
        'clear and dry',
        'hot and hazy, air shimmering',
        'heavy grey overcast',
        'light drizzle',
        'just after heavy rain, everything wet and reflective',
        'thick fog or low cloud',
        'dust or sand haze in the air',
        'falling snow',
        'old snow on the ground, grey sky',
        'strong wind moving everything loose',
        'storm clouds breaking apart, patchy dramatic light',
        'humid and overcast, monsoon-heavy air',
        'crisp and cold, breath visible',
        'smoke or cooking haze hanging in the air',
    ]
    return random.choice(weather)


# Framing recipes pair a shot distance with a plausible focal length and camera
# position, so the combination always makes photographic sense.
def get_framing():
    framings = [
        'extreme wide establishing shot on a 14mm ultra-wide lens, camera at eye level, everything in deep focus',
        'wide environmental shot on a 24mm lens from a low, near-ground camera position',
        'wide shot on a 28mm lens taken from a high vantage point looking down',
        'wide shot on a 24mm lens from an aerial drone position well above the scene',
        'standard 35mm reportage framing at eye level, subject off-centre',
        'standard 50mm framing, shallow-ish depth of field, background falling away softly',
        'medium shot on an 85mm lens, subject isolated against a soft background',
        'tight telephoto shot on a 135mm lens, layers of the scene compressed together',
        'long 200mm telephoto shot compressing distant elements into flat stacked planes',
        'close detail shot at minimum focus distance, very shallow depth of field',
        'shot framed through a doorway, window or archway, foreground darkness surrounding the scene',
        'shot from inside a moving vehicle through the window, frame partly obstructed',
        'over-the-shoulder framing, a person in the near foreground out of focus',
        'waist-level framing on a 40mm lens, slightly tilted, taken quickly without looking',
    ]
    return random.choice(framings)


# The physical medium does more to change the look of an image than any
# abstract style label, so this replaces the old free-floating "style" list.
def get_medium_look():
    looks = [
        'clean modern full-frame digital capture, neutral colour, very high detail',
        'Kodak Portra 400 35mm film, soft warm skin tones, gentle grain',
        'Kodak Gold 200 35mm film, warm yellows, slight halation in highlights',
        'Fujifilm Velvia slide film, deeply saturated greens and blues, high contrast',
        'Ilford HP5 black and white 35mm film, coarse grain, strong contrast',
        'Kodak Tri-X black and white film, classic documentary grain',
        'CineStill 800T at night, tungsten colour cast, red halation around light sources',
        'medium format 6x7 film, extremely fine detail, smooth tonal gradation',
        'direct on-camera flash at night, harsh foreground, dark falloff behind',
        'expired film, shifted colours, uneven casts, light leak at one edge',
        'instant film print, soft focus, muted washed-out palette, slight vignette',
        '16mm documentary film still, grainy, slightly desaturated',
        'handheld smartphone snapshot, slight motion blur, imperfect exposure',
        'large format 4x5 view camera, immense detail, perfectly level horizon',
        'infrared film, foliage rendered pale and luminous',
        'long exposure on a tripod, moving elements smeared into soft trails',
    ]
    return random.choice(looks)


# Phrased positively on purpose. FLUX.2 doesn't process negation - "no people"
# reliably produces people - so emptiness is described as a deserted place
# rather than as an absence.
def get_human_presence():
    presence = [
        'completely deserted, the empty setting alone',
        'a single person small in the frame, incidental, back turned to the camera',
        'one person as the clear subject, an unposed environmental portrait, aware of the camera',
        'one person absorbed in a task, unaware of the camera',
        'two or three people mid-conversation or mid-activity',
        'a small group working or eating together',
        'a busy crowd filling the frame, many partial faces',
        'deserted, with fresh traces of someone who has just left - a tool set down, a door left open',
    ]
    return random.choice(presence)


# Fame tiers are weighted hard away from the obvious landmark. Without this the
# model returns the same handful of postcard sites for every country.
FAME_TIERS = [
    ('the single most internationally famous site in the country', 10),
    ('a well-known place that domestic tourists would recognise, but not the top international landmark', 25),
    ('somewhere known mainly within its own region or province', 35),
    ('an entirely ordinary, unremarkable place with no fame at all - the kind of spot nobody photographs', 30),
]


def get_fame_tier():
    tiers = [tier for tier, _ in FAME_TIERS]
    weights = [weight for _, weight in FAME_TIERS]
    return random.choices(tiers, weights=weights, k=1)[0]


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
        "People & Everyday Culture",
        "Work & Trade",
        "Transport & Roads",
        "Religion & Ritual",
        "Sport & Play",
        "Homes & Interiors",
        "Festivals & Celebration",
        "Water & Rivers",
        "Industry & Infrastructure",
        "Night Life After Dark",
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


def get_random_country(fileName, recent_countries=None):
    with open(fileName, 'r') as file:
        countries = [line.strip() for line in file if line.strip()]

    recent_countries = set(recent_countries or [])

    weights = [POPULAR_COUNTRY_WEIGHT if country in POPULAR_COUNTRIES else 1
               for country in countries]

    # Suppress countries used very recently so the feed doesn't sit in one
    # place for a run of posts, without excluding them outright.
    weights = [w * 0.05 if country in recent_countries else w
               for country, w in zip(countries, weights)]

    return random.choices(countries, weights=weights, k=1)[0]


def load_prompts(config_file="data/prompts.json"):
    with open(config_file, 'r') as f:
        return json.load(f)


def load_config(config_file="data/config.json"):
    with open(config_file, 'r') as f:
        return json.load(f)


# --- Post history -----------------------------------------------------------
# Without this, nothing stops the same country and landmark reappearing. The
# history is fed back into the prompt as an explicit exclusion list.

HISTORY_FILE = "data/history.json"
HISTORY_LIMIT = 400
RECENT_COUNTRY_WINDOW = 25
RECENT_SUBJECT_WINDOW = 40


def load_history(history_file=HISTORY_FILE):
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    return history if isinstance(history, list) else []


def save_history_entry(entry, history_file=HISTORY_FILE):
    history = load_history(history_file)
    history.append({**entry, "timestamp": datetime.now(timezone.utc).isoformat()})
    history = history[-HISTORY_LIMIT:]

    os.makedirs(os.path.dirname(history_file) or ".", exist_ok=True)
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)


def get_recent_countries(history, window=RECENT_COUNTRY_WINDOW):
    return [entry.get("country") for entry in history[-window:] if entry.get("country")]


def get_exclusions(history, country, subject_window=RECENT_SUBJECT_WINDOW):
    """Places already used in this country (ever), plus subjects used recently
    anywhere - the latter stops every post becoming a market stall."""
    used_locations = [entry.get("location") for entry in history
                      if entry.get("country") == country and entry.get("location")]

    recent_subjects = [entry.get("subject") for entry in history[-subject_window:]
                       if entry.get("subject")]

    return used_locations, recent_subjects


def format_exclusions(used_locations, recent_subjects):
    lines = []

    if used_locations:
        lines.append(
            "These places in this country have already been posted - do not choose any of them again:\n"
            + "\n".join(f"- {location}" for location in used_locations))

    if recent_subjects:
        lines.append(
            "These subjects were used in recent posts for other countries - avoid anything closely similar:\n"
            + "\n".join(f"- {subject}" for subject in recent_subjects))

    if not lines:
        return "No previous posts to avoid."

    return "\n\n".join(lines)


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
