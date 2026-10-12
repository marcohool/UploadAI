import os
import random
import urllib.request
import json
from datetime import datetime, timezone

from PIL import Image, ImageOps

from utils.json_processing import process_caption_facts, process_caption_response
from utils.prompt_cleanup import (DEFAULT_HASHTAG_COUNT, caption_issues,
                                  clean_caption, normalise_hashtags,
                                  split_trailing_hashtags)


# Every axis below is sampled here in Python rather than left to the language
# model. Asked to choose freely, the model returns its favourite answer almost
# every time (golden hour, 24mm, the same landmark), which is what makes a feed
# look repetitive. Sampling here forces genuine spread.
#
# Every option on every axis has to be capable of producing a photograph worth
# stopping for. The account is called World's Wonders: variety comes from which
# wonder and how it is seen, never from making it look worse. An earlier version
# sampled drizzle, expired film, phone snapshots and "the kind of spot nobody
# photographs" independently, so only about one post in fifty drew a good place
# in good light on a flattering medium - and that is exactly how the feed looked.


# Light and weather are one axis, offered as a shortlist the model chooses from.
# Sampled independently and imposed, they produced snow in Hoi An and fog-bound
# night shots of courtyards. The model knows which of a few beautiful options is
# plausible for this place and season; it just mustn't pick from all of them, or
# it picks golden hour every time.
LIGHT_CONDITIONS = [
    'first light, the sun just clearing the horizon and raking low across the subject',
    'golden hour, warm low sun lighting the subject from the side',
    'sunset, the sky lit up with colour in high broken cloud',
    'blue hour just after sunset, a deep blue sky with lights just switched on',
    'soft early morning, mist lying in the valleys and over water',
    'a clearing storm, shafts of sunlight breaking through dark cloud onto the subject',
    'bright clear day, deep blue sky, clear true colour in water and foliage',
    'soft overcast light after rain, wet rock and rich deep greens',
    'clear night, the Milky Way overhead, the landscape faintly lit by starlight',
    'fresh snow under a clear sky, crisp cold light',
    'the aurora overhead, green curtains reflected in the landscape below',
    'low cloud wrapping the peaks and towers, sunlight breaking through above it',
    'a sea of cloud filling the valleys below, the subject rising clear above it in early light',
    'warm late afternoon light at the peak of autumn colour',
    'spring, the landscape in blossom or full fresh green, under soft bright light',
]

LIGHT_OPTION_COUNT = 3


def get_light_options(count=LIGHT_OPTION_COUNT):
    return random.sample(LIGHT_CONDITIONS, count)


# Composition recipes pair a viewpoint with a plausible focal length, and every
# one of them is a way professional travel photographers make a place look its
# most impressive - depth, scale, reflection, leading lines. Offered as a
# shortlist for the same reason as the light: imposed, they produced viewpoints
# that can't exist (Mount Misen behind the Miyajima torii, seen from the shore),
# and the image model invents what it has never seen from that angle.
FRAMINGS = [
    'grand wide vista from an elevated viewpoint on a 16-35mm lens, layers receding from a detailed foreground to the horizon',
    'low ultra-wide angle on a 14-20mm lens, strong foreground interest close to the camera leading the eye to the subject',
    'aerial drone view from high above, revealing the shape and scale of the place',
    'top-down aerial drone shot looking straight down, the subject making a graphic pattern',
    'mirror reflection of the subject in still water, the horizon placed off-centre',
    'telephoto compression on a 70-200mm lens, the subject stacked against layers of landscape behind it',
    'a leading line - a road, river, path, wall or ridge - drawing the eye from the bottom corner of the frame to the subject',
    'framed by a natural or architectural opening - an arch, a cave mouth, a window, overhanging branches',
    'vertical composition emphasising height, the subject rising from the bottom of the frame to the top',
    'standard 35mm lens at eye level, as a visitor first sees it on arrival, the subject placed on a third',
]

FRAMING_OPTION_COUNT = 3


def get_framing_options(count=FRAMING_OPTION_COUNT):
    return random.sample(FRAMINGS, count)


# Rendering styles that read as a professional photograph with natural colour.
# Expired film, B&W, smartphone and instant-film looks are gone - they made a
# feed of wonders look like a feed of mistakes. "Saturated" is kept out of every
# option: oversaturation is the first thing that makes an image read as AI.
def get_medium_look():
    looks = [
        'high-resolution full-frame mirrorless camera, crisp edge-to-edge detail, natural true-to-life colour',
        'medium format digital camera, immense fine detail, smooth tonal gradation, rich natural colour',
        'Fujifilm Velvia slide film, rich clean blues and greens, crisp contrast',
        'Kodak Portra 400 film, warm soft tones, fine grain',
        'Kodak Ektar 100 film, vivid but natural colour, ultra-fine grain',
        'long exposure on a tripod, moving water and cloud smoothed to silk, everything still pin-sharp',
    ]
    return random.choice(looks)


# Phrased positively on purpose. FLUX.2 doesn't process negation - "no people"
# reliably produces people - so emptiness is described as a deserted place
# rather than as an absence. A small figure is the most common option: it's what
# makes a landscape read as immense rather than as a hill, and posts with a
# person in them get liked more. It only works if it reads at phone size, hence
# the open background.
HUMAN_PRESENCE = [
    ('the place alone, undisturbed and deserted', 30),
    ('one small figure, back to the camera, set against open sky, water, sand or snow so it reads clearly, showing the scale of the place', 40),
    ('a few people far off, small and incidental', 15),
    ('local people at the heart of the scene - a boatman, pilgrims, herders, festival-goers - absorbed in what they are doing', 15),
]


def get_human_presence():
    presence = [option for option, _ in HUMAN_PRESENCE]
    weights = [weight for _, weight in HUMAN_PRESENCE]
    return random.choices(presence, weights=weights, k=1)[0]


# Every tier has to be spectacular - the tiers vary how well known the place is,
# never how good it looks. The famous wonders are what people recognise and stop
# for; the lesser-known ones are what make them follow ("where is this?").
FAME_TIERS = [
    ('one of the world-famous wonders this country is known for - the landmark or landscape on the cover of its guidebook', 35),
    ('a spectacular place that well-travelled photographers know but most people abroad have never heard of - every bit as striking as the famous sites, the kind of view that makes someone ask "where is this?"', 45),
    ('a beautiful place famous within the country itself, where domestic travellers go for the view, but rarely seen abroad', 20),
]


def get_fame_tier():
    tiers = [tier for tier, _ in FAME_TIERS]
    weights = [weight for _, weight in FAME_TIERS]
    return random.choices(tiers, weights=weights, k=1)[0]


def is_landmark_tier(tier):
    return tier == FAME_TIERS[0][0]


def get_shot_category():
    shot_categories = [
        "Iconic Landmark or Monument",
        "Ancient Ruins & Archaeological Sites",
        "Temples, Mosques, Cathedrals & Monasteries",
        "Palaces, Castles & Fortresses",
        "Historic Old Town or Village",
        "City Skyline or Waterfront",
        "Mountains & High Peaks",
        "Coastline, Sea Cliffs & Beaches",
        "Islands, Reefs & Lagoons",
        "Waterfalls, Rivers & Gorges",
        "Lakes & Glaciers",
        "Deserts & Dunes",
        "Forests, Jungles & Rainforest",
        "Volcanic & Geothermal Landscapes",
        "Canyons, Caves & Rock Formations",
        "Terraced Fields, Plantations & Cultivated Landscapes",
        "Wildlife in its Natural Habitat",
        "Festivals & Celebrations",
        "Night Sky over a Landscape",
        "Bridges, Roads & Railways through Dramatic Scenery",
    ]
    return random.choice(shot_categories)


# --- Caption axes -----------------------------------------------------------
# Captions are sampled along two axes rather than one. The angle decides what
# the caption is about; the shape decides how it sits on the screen. Varying
# only the angle still produces a feed where every post has the same silhouette,
# which reads as templated however good the writing is.

# Every angle is something a person looking at a wonder would actually want to
# know. The old list was written for deliberately ordinary places - the
# economics of a loading bay, the routine of whoever walks past it - and
# produced captions about drainage and motorbike parking.
CAPTION_ANGLES = [
    'one surprising fact about this place, stated flatly and then explained',
    'the scale of this place made concrete with a number or comparison that changes how the photo reads',
    'how this place was formed or built - the forces, the people, how long it took',
    'the legend, myth or belief attached to this place, and what is actually true behind it',
    'a record this place holds - oldest, largest, deepest, highest, only - and what it means in practice',
    'where the name came from and what it originally meant',
    'one specific thing that happened here, told as a short story',
    'what this place was before it became famous, and what changed',
    'the detail most visitors walk straight past, and why it is there',
    'a widely held assumption about this place that turns out to be wrong',
    'how close this place came to being lost or destroyed, and what saved it',
    'the moment, hour or season when this place is at its best, and why',
]

# Every shape opens with the hook alone on the first line. Instagram shows
# little more than that before "more", and a hook run straight into a paragraph
# spends the preview on half a sentence. None ends on a "turn" - asked for one,
# the model writes an aphorism ("The drama is structural, not symbolic.").
CAPTION_SHAPES = [
    'the hook alone on the first line, a blank line, then one paragraph that pays it off',
    'the hook alone on the first line, a blank line, then three short beats, each on its own line',
    'a statement that sounds wrong alone on the first line, a blank line, then the explanation that makes it true',
    'the hook alone on the first line, a blank line, then what happened, told in two or three short sentences',
    'the hook alone on the first line, a blank line, then three related details listed one per line, no conclusion',
]

RECENT_ANGLE_WINDOW = 8


def get_caption_angle(recent_angles=None):
    recent_angles = set(recent_angles or [])

    # Damped rather than excluded, the same way recent countries are, so a
    # short history doesn't force the same handful of angles round in rotation
    weights = [0.05 if angle in recent_angles else 1.0 for angle in CAPTION_ANGLES]

    return random.choices(CAPTION_ANGLES, weights=weights, k=1)[0]


def get_caption_shape():
    return random.choice(CAPTION_SHAPES)


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


# The scout ranks its own candidates for visual impact. Picking at random from
# all twelve let the weakest ideas through as often as the best; always taking
# the top one would bring back the model's favourite. Random among the top few
# keeps both the quality and the spread.
TOP_CANDIDATES = 4


def pick_candidate(candidates, top=TOP_CANDIDATES, exists=None, used_locations=()):
    """One of the strongest candidates, skipping any that `exists` rejects.

    A convincing photograph of a place that doesn't exist is the one thing this
    account must never post - people plan trips around travel photos. If every
    check fails it's more likely the geocoder is down than that all four places
    are invented, so a candidate is still returned rather than losing the post.
    """
    # The scout is told which places have been posted, but a repeat costs
    # nothing to catch here as well
    used = {location.strip().lower() for location in used_locations}
    fresh = [c for c in candidates if c["location"].strip().lower() not in used]
    pool = fresh or list(candidates)

    # Shuffled before the (stable) sort so ties at the cut-off aren't settled by
    # the order the model happened to list them in
    random.shuffle(pool)
    ranked = sorted(pool, key=lambda c: c["visual_impact"], reverse=True)[:top]
    random.shuffle(ranked)

    if exists is None:
        return ranked[0]

    for candidate in ranked:
        if exists(candidate["location"]):
            return candidate
        print(f"Couldn't find {candidate['location']!r} on a map - skipping it")

    print("No candidate could be found on a map - using one anyway")
    return ranked[0]


def load_prompts(config_file="data/prompts.json"):
    with open(config_file, 'r') as f:
        return json.load(f)


def load_config(config_file="data/config.json"):
    with open(config_file, 'r') as f:
        return json.load(f)


# --- Post history -----------------------------------------------------------
# Without this, nothing stops the same country and landmark reappearing. The
# history is fed back into the prompt as an explicit exclusion list.

HISTORY_FILE = "data/state/history.json"
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


# Instagram's portrait feed size. A 4:5 post takes a quarter more of the screen
# than a square one, and at exactly this size neither instagrapi nor Instagram
# needs to resize or crop it. instagrapi still re-encodes the JPEG at Pillow's
# default quality before upload, so the high-quality save here just avoids
# stacking a second lossy pass on top of that.
INSTAGRAM_SIZE = (1080, 1350)


def fit_for_instagram(imageFileName, size=INSTAGRAM_SIZE):
    with Image.open(imageFileName) as image:
        image = ImageOps.fit(image.convert("RGB"), size, Image.Resampling.LANCZOS)
        image.save(imageFileName, "JPEG", quality=95, subsampling=0)


def handle_image_generation(image_model, prompt, imageFileName):
    generatedImageLink = image_model.generate_image(prompt)
    print("\nImage generated -> ", generatedImageLink)

    # Download image
    os.makedirs(os.path.dirname(imageFileName) or ".", exist_ok=True)
    urllib.request.urlretrieve(
        generatedImageLink, imageFileName)

    fit_for_instagram(imageFileName)

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


def with_country(location, country):
    """The scout writes locations as "Place, Country", sometimes spelling the
    country differently from countryList.txt ("USA", "Côte d'Ivoire"). Only a
    bare place name gets the country added, or it would appear twice."""
    if "," in location or country.lower() in location.lower():
        return location

    return f"{location}, {country}"


def alt_text(subject, location, country):
    """Instagram's alt text is read by screen readers and by Instagram search.
    The scout's subject line is already a plain description of the frame."""
    return f"{subject.rstrip('.')}. {with_country(location, country)}."


def location_line(location, country):
    """The pin line under the caption. Travel accounts put the place there so
    it can be read at a glance - and so it's searchable text, which a geotag
    alone isn't."""
    return f"\U0001F4CD {with_country(location, country)}"


def generate_caption(text_model, prompts, *, location, country, subject,
                     shot_category, angle, shape):
    facts = research_caption_facts(
        text_model, prompts, location, country, subject)
    print(f"Researched {len(facts)} caption facts -> ", facts)

    prompt = prompts['caption_prompt'].format(
        chosenLocation=location, subject=subject, shotCategory=shot_category,
        facts=format_facts(facts), captionAngle=angle, captionShape=shape,
        hashtagCount=DEFAULT_HASHTAG_COUNT)

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

    caption = (f"{clean_caption(body)}\n\n{location_line(location, country)}\n\n"
               f"{normalise_hashtags(hashtags)}")

    print("Caption generated -> ", caption)

    return caption
