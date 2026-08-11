import os
import random
import urllib.request
import json
from datetime import datetime, timezone

from utils.json_processing import process_caption_facts, process_caption_response
from utils.prompt_cleanup import (caption_issues, clean_caption,
                                  normalise_hashtags, split_trailing_hashtags)


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


# Fame tiers are weighted away from the obvious landmark. Without this the model
# returns the same handful of postcard sites for every country. The top tier is
# kept deliberately - a feed of nothing but obscure places has no anchor, and
# the famous sites are what people recognise and stop for.
FAME_TIERS = [
    ('one of the handful of internationally famous sites the country is actually known for - the capital\'s landmark quarter, the national monument, the view on the cover of the guidebook', 10),
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


# --- Caption axes -----------------------------------------------------------
# Captions are sampled along two axes rather than one. The angle decides what
# the caption is about; the shape decides how it sits on the screen. Varying
# only the angle still produces a feed where every post has the same silhouette,
# which reads as templated however good the writing is.

CAPTION_ANGLES = [
    'one surprising fact about this place, stated flatly and then explained',
    'where the name of this place came from and what it originally meant',
    'one specific thing that happened here, told as a short story',
    'why the place is built or shaped the way it is - the practical reason behind what is visible',
    'a local custom, rule or etiquette around this place that an outsider would get wrong',
    'the scale of what is here, made concrete with a number or a comparison that changes how the photo reads',
    'the unnamed person whose daily routine runs through this place, and what their day around it looks like',
    'what this place was before it was this, and what changed it',
    'a widely held assumption about this place that turns out to be wrong',
    'the small detail in the frame most people would walk straight past, and why it is there',
    'the gap between how the people who live here use this place and how visitors assume it is used',
    'what this place is like at a completely different hour or season from the one photographed',
    'a word or phrase used here that English has no clean equivalent for',
    'the economics of what is in the frame - who pays for it, who profits, where it ends up',
    'what sits just outside the frame, and why it matters to what is inside it',
]

CAPTION_SHAPES = [
    'one unbroken paragraph, no line breaks at all, opening on a short sentence and then running quickly',
    'a single blunt line on its own, a blank line, then one paragraph that pays it off',
    'three short beats, each on its own line, no paragraph anywhere',
    'a statement that sounds wrong, a blank line, then the explanation that makes it true',
    'a bare number or year alone on the first line, then the context underneath it - only if the researched material actually contains one, otherwise a short flat statement on that first line instead',
    'two lines of setup, a blank line, then one short line that turns it',
    'three related details listed one per line, no preamble and no conclusion',
    'one very short line, then one long winding sentence that unpacks it',
    'a question in the first line answered immediately in the second, then a paragraph that complicates the answer',
]

RECENT_ANGLE_WINDOW = 8
CAPTION_QUESTION_RATE = 0.33

# An engagement question every post becomes its own tic, so it is sampled too.
CAPTION_QUESTION_INSTRUCTION = (
    "End on one genuine question about the specific thing this caption is "
    "about - something a reader could actually answer or hold an opinion "
    "about. No rhetorical questions, nothing abstract, nothing about how the "
    "reader feels. Not \"have you been?\", not \"would you visit?\", and not a "
    "request to comment, save or share. If no real question comes out of this "
    "material, end on the content instead rather than forcing one.")

CAPTION_NO_QUESTION_INSTRUCTION = (
    "Do not end with a question, and do not ask anybody to comment, save or "
    "share. End on the content itself.")


def get_caption_angle(recent_angles=None):
    recent_angles = set(recent_angles or [])

    # Damped rather than excluded, the same way recent countries are, so a
    # short history doesn't force the same handful of angles round in rotation
    weights = [0.05 if angle in recent_angles else 1.0 for angle in CAPTION_ANGLES]

    return random.choices(CAPTION_ANGLES, weights=weights, k=1)[0]


def get_caption_shape():
    return random.choice(CAPTION_SHAPES)


def should_ask_question():
    return random.random() < CAPTION_QUESTION_RATE


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


def get_recent_caption_angles(history, window=RECENT_ANGLE_WINDOW):
    return [entry.get("caption_angle") for entry in history[-window:]
            if entry.get("caption_angle")]


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


def handle_image_generation(image_model, prompt, imageFileName):
    generatedImageLink = image_model.generate_image(prompt)
    print("\nImage generated -> ", generatedImageLink)

    # Download image
    os.makedirs(os.path.dirname(imageFileName) or ".", exist_ok=True)
    urllib.request.urlretrieve(
        generatedImageLink, imageFileName)

    return imageFileName


# --- Captions ---------------------------------------------------------------
# Written from the location and researched facts rather than from the image
# prompt. Describing the photo back to somebody who is already looking at it
# adds nothing, which is what made the old captions interchangeable.


def format_facts(facts):
    if not facts:
        return "No researched material was available for this location."

    return "\n".join(f"- ({fact['scope']}) {fact['fact']}" for fact in facts)


def research_caption_facts(text_model, prompts, location, country, subject):
    """Source the material the caption will be built from.

    Run at a low temperature on purpose - this is the one call where invention
    is the failure mode rather than the point. A failure here is survivable:
    the caption falls back to writing from the angle alone rather than losing
    the whole post.
    """
    try:
        facts_json = text_model.get_text_response(0.4, prompts['caption_facts_prompt'].format(
            chosenLocation=location, randomCountry=country, subject=subject))

        return process_caption_facts(facts_json)
    except Exception as e:
        print("Couldn't research caption facts, writing without them: ", e)
        return []


CAPTION_MAX_ATTEMPTS = 3

CAPTION_RETRY_NOTE = (
    "\n\nA previous attempt at this caption was rejected because:\n{issues}\n\n"
    "Write a different caption that avoids all of those. Do not reword the old "
    "one around the problem - the rejected phrasing was usually holding up a "
    "sentence that had nothing else in it.")


def _read_caption(text_model, prompt):
    body, hashtags = process_caption_response(
        text_model.get_text_response(1.0, prompt))

    # Hashtags land in the caption field about as often as in the array they
    # were asked for, so they're pulled back out either way
    body, inline_hashtags = split_trailing_hashtags(body)

    return body, hashtags or inline_hashtags


def generate_caption(text_model, prompts, *, location, country, subject,
                     shot_category, angle, shape, ask_question):
    facts = research_caption_facts(
        text_model, prompts, location, country, subject)
    print(f"Researched {len(facts)} caption facts -> ", facts)

    prompt = prompts['caption_prompt'].format(
        chosenLocation=location, subject=subject, shotCategory=shot_category,
        facts=format_facts(facts), captionAngle=angle, captionShape=shape,
        questionInstruction=(CAPTION_QUESTION_INSTRUCTION if ask_question
                             else CAPTION_NO_QUESTION_INSTRUCTION))

    # The banned constructions can't be stripped the way a stray adjective can,
    # because the sentence is built around them - the caption has to be written
    # again. The model is stubborn about "is not just X, it's Y" in particular
    # and sometimes needs telling twice. Whatever the last attempt produced
    # still goes out: a slightly clichéd post beats no post.
    body, hashtags = _read_caption(text_model, prompt)

    for attempt in range(CAPTION_MAX_ATTEMPTS - 1):
        issues = caption_issues(body, facts)
        if not issues:
            break

        print(f"Caption rejected (attempt {attempt + 1}) -> ", issues)
        body, hashtags = _read_caption(text_model, prompt + CAPTION_RETRY_NOTE.format(
            issues="\n".join(f"- {issue}" for issue in issues)))
    else:
        if caption_issues(body, facts):
            print("Caption still not clean, posting it anyway -> ",
                  caption_issues(body, facts))

    caption = f"{clean_caption(body)}\n\n\n{normalise_hashtags(hashtags)}"

    print("Caption generated -> ", caption)

    return caption
