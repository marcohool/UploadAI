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


# --- Content pillars ---------------------------------------------------------
# Every post belongs to one of four kinds - nature, a city, a landmark or a
# spectacle - and the kinds take turns, one of each in every four posts. Drawing a shot category at random from
# one flat list made nature two posts in three, because most of the categories
# were landscapes, and every light, composition and people option was written
# for landscapes too. Even a city post came out as a deserted view at dawn with
# one hiker in it, so six posts in a row looked like the same mountain trip.
#
# Each pillar has its own categories, light, compositions, renderings and
# people, because what makes a city photograph (lit windows after rain, the
# life of the street) is nothing like what makes a mountain one (mist in the
# valleys, a figure for scale). Light and composition are still offered as a
# shortlist the model picks a plausible option from. Imposed outright, they
# produced snow in Hoi An and viewpoints that can't exist, and left to choose
# freely the model picks golden hour every time.
#
# Every option has to be capable of a photograph worth stopping for. The
# account is called World's Wonders: variety comes from which wonder and how
# it is seen, never from making it look worse. An earlier version sampled
# drizzle, expired film and phone snapshots, and the feed looked like it.
# "Saturated" is kept out of every rendering - oversaturation is the first thing
# that makes an image read as AI.
#
# People are phrased positively on purpose. Image models handle negation badly
# - "no people" reliably produces people - so emptiness is described as a
# deserted place rather than as an absence.

_LANDSCAPE_FRAMINGS = [
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

_LANDSCAPE_LOOKS = [
    'high-resolution full-frame mirrorless camera, crisp edge-to-edge detail, natural true-to-life colour',
    'medium format digital camera, immense fine detail, smooth tonal gradation, rich natural colour',
    'Fujifilm Velvia slide film, rich clean blues and greens, crisp contrast',
    'Kodak Portra 400 film, warm soft tones, fine grain',
    'Kodak Ektar 100 film, vivid but natural colour, ultra-fine grain',
]

PILLARS = {
    'nature': {
        'brief': 'a natural wonder - a landscape, seascape or natural feature unlike anywhere else, with the land itself as the subject',
        'categories': [
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
            "Night Sky over a Landscape",
        ],
        'light': [
            'first light, the sun just clearing the horizon and raking low across the subject',
            'golden hour, warm low sun lighting the subject from the side',
            'sunset, the sky lit up with colour in high broken cloud',
            'soft early morning, mist lying in the valleys and over water',
            'a clearing storm, shafts of sunlight breaking through dark cloud onto the subject',
            'bright clear day, deep blue sky, clear true colour in water and foliage',
            'soft overcast light after rain, wet rock and rich deep greens',
            'clear night, the Milky Way overhead, the landscape faintly lit by starlight',
            'fresh snow under a clear sky, crisp cold light',
            'the aurora overhead, green curtains reflected in the landscape below',
            'a sea of cloud filling the valleys below, the subject rising clear above it in early light',
            'warm late afternoon light at the peak of autumn colour',
            'spring, the landscape in blossom or full fresh green, under soft bright light',
        ],
        'framings': _LANDSCAPE_FRAMINGS,
        'looks': _LANDSCAPE_LOOKS + [
            'long exposure on a tripod, moving water and cloud smoothed to silk, everything still pin-sharp',
        ],
        # A small figure is the most common option: it's what makes a landscape
        # read as immense rather than as a hill. It only works if it reads at
        # phone size, hence the open background.
        'people': [
            ('the place alone, undisturbed and deserted', 35),
            ('one small figure, back to the camera, set against open sky, water, sand or snow so it reads clearly, showing the scale of the place', 40),
            ('a few people far off, small and incidental', 15),
            ('local people at work in the landscape - a boatman, herders, farmers - absorbed in what they are doing', 10),
        ],
    },
    'city': {
        'brief': 'a city as a living place - its skyline, streets, rooftops, waterfronts and the life in them. The city itself is the subject, not a single monument in it, and it is a real city or large town, not a village',
        'categories': [
            "City Skyline at Night or Blue Hour",
            "A City from Above - Rooftops, Domes & Street Grids",
            "Old Town Streets, Alleys & Stairways",
            "Canals, Harbours & Waterfronts",
            "Markets, Night Markets & Street Life",
            "Colourful Neighbourhoods & Painted Houses",
            "Modern Architecture & Futuristic Cityscapes",
            "Cities Built on Hillsides, Cliffs or Water",
        ],
        'light': [
            'blue hour, a deep blue sky with every window and street lamp lit',
            'night after rain, the wet streets mirroring the glow of lanterns, shop windows and coloured lights',
            'golden hour, low warm sun lighting the facades and catching the tops of the towers',
            'sunset behind the skyline, the buildings dark against a sky full of colour',
            'first light, the streets still quiet and the facades warming in the low sun',
            'low cloud drifting through the towers, their tops breaking through into clear sky',
            'clear night, the whole city lit up beneath a dark sky',
            'snow falling at night, lit by warm street lamps and windows',
            'bright clear morning, deep blue sky and true colour on painted walls',
            'dusk, lanterns and string lights coming on along the street',
        ],
        'framings': [
            'the skyline seen across water from the far shore, its lights reflected in the water',
            'from a high viewpoint over the rooftops on a 24-70mm lens, the roofscape running to the horizon',
            'aerial drone view looking down into the street grid, canals or tangle of rooftops',
            'street level on a 35mm lens, looking along a street, canal or stairway that leads the eye deep into the scene',
            'telephoto compression on a 70-200mm lens, buildings stacked one behind another up a hillside or along the water',
            'looking up from the street between tall buildings, their lines converging into the sky',
            'from a rooftop or balcony looking down into the life of the street below',
            'framed by an archway, a window or the gap between two buildings',
        ],
        'looks': [
            'high-resolution full-frame mirrorless camera, crisp detail, true-to-life colour',
            'CineStill 800T film, tungsten-balanced colour, soft halation around the lights',
            'Kodak Portra 400 film, warm soft tones, fine grain',
            'Kodak Ektar 100 film, vivid but natural colour, ultra-fine grain',
            'long exposure on a tripod, traffic drawn into trails of light and water smoothed, every building pin-sharp',
        ],
        'people': [
            ('the everyday life of the city - people walking, cycling, trading and talking, as many as there really would be at that place and hour', 45),
            ('the streets almost empty at a quiet hour, one or two people passing through', 20),
            ('one local in the foreground - a vendor, a cyclist, someone climbing the steps - small enough that the city still fills the frame', 15),
            ('the city seen from above or from afar, its people too small to pick out', 20),
        ],
        # Countries with no city or town that would carry a city post. Drawn
        # for one, the scout reaches for the only street there is, or drifts
        # back into a landscape.
        'skip_countries': {
            "Kiribati", "Marshall Islands", "Micronesia", "Nauru", "Palau",
            "Solomon Islands", "Tuvalu", "Tonga", "Samoa", "Vanuatu",
            "Central African Republic", "Chad", "South Sudan",
        },
    },
    'landmark': {
        'brief': 'one great built wonder - a monument, temple, castle, palace, ruin or bridge - as the unmistakable hero of the photograph',
        'categories': [
            "Iconic Landmark or Monument",
            "Ancient Ruins & Archaeological Sites",
            "Temples, Mosques, Cathedrals & Monasteries",
            "Palaces, Castles & Fortresses",
            "Bridges, Roads & Railways through Dramatic Scenery",
            "Grand Interiors - Domes, Halls, Libraries & Stations",
        ],
        'light': [
            'first light, the sun just clearing the horizon and raking across the stone',
            'golden hour, warm low sun lighting the building from the side',
            'sunset, the sky lit up with colour in high broken cloud',
            'blue hour, the building floodlit against a deep blue sky',
            'soft early morning, mist lying around its base',
            'a clearing storm, sunlight breaking through dark cloud onto the building',
            'bright clear day, deep blue sky, clear true colour in stone and tile',
            'fresh snow on the roofs and grounds under a clear sky',
            'clear night, the Milky Way above a remote ruin',
            'sunlight falling in shafts through high windows into the interior',
        ],
        'framings': _LANDSCAPE_FRAMINGS + [
            'perfect symmetry, looking straight down the central axis of the building',
            'inside, looking up into the dome or vault from beneath it',
        ],
        'looks': _LANDSCAPE_LOOKS,
        'people': [
            ('the place alone, undisturbed and deserted', 30),
            ('one small figure, back to the camera, showing the scale of the building', 30),
            ('a few people far off, small and incidental', 20),
            ('the people it was built for at the heart of the scene - pilgrims, monks, worshippers - absorbed in what they are doing', 20),
        ],
    },
    'spectacle': {
        'brief': 'something extraordinary that happens or can be found here - a festival, a natural phenomenon at its peak, a wildlife spectacle, a shipwreck, an abandoned or surreal place, a living tradition. The photograph that makes people ask "is that real?" - and it is: real, documented, and something a photographer could actually witness there',
        'categories': [
            "Festivals, Processions & Celebrations",
            "Natural Phenomena at Their Peak - bioluminescence, fireflies, desert blooms, flowing lava, erupting geysers, ice caves",
            "Wildlife Spectacles - migrations, vast flocks and herds, breaching whales",
            "Shipwrecks, Sunken Wonders & Underwater Worlds",
            "Abandoned, Overgrown & Surreal Places",
            "Living Traditions - crafts, ways of life and ways of travel still practised",
            "Engineering Feats & Extreme Structures",
        ],
        'light': [
            'night, the scene lit by its own light - fire, lanterns, lava or glowing water',
            'blue hour, a deep blue sky and the first lights of the evening',
            'golden hour, warm low sun lighting the scene from the side',
            'first light, mist still lying low over the scene',
            'bright clear day, deep blue sky and true colour',
            'a clearing storm, shafts of sunlight breaking through dark cloud',
            'underwater, sunlight falling in shafts through clear blue water',
            'clear night, the Milky Way overhead',
            'soft overcast light, rich true colour with nothing burnt out',
        ],
        'framings': [
            'in among it at eye level on a 24-35mm lens, the action filling the frame',
            'from an elevated viewpoint on a 16-35mm lens, showing the whole scene and its scale',
            'aerial drone view from high above, revealing the shape and scale of the scene',
            'telephoto compression on a 70-200mm lens, the subject stacked against what lies behind it',
            'low ultra-wide angle on a 14-20mm lens, strong foreground interest close to the camera leading the eye to the subject',
            'underwater wide angle on a 14-16mm lens, the subject looming out of the blue',
            'framed by a natural or architectural opening - an arch, a doorway, a broken window, overhanging branches',
        ],
        'looks': _LANDSCAPE_LOOKS + [
            'CineStill 800T film, tungsten-balanced colour, soft halation around the lights',
        ],
        'people': [
            ('the people at the heart of it - festival-goers, herders, fishermen, divers - absorbed in what they are doing', 45),
            ('the scene alone, undisturbed and deserted', 30),
            ('one small figure watching, back to the camera, showing the scale of it', 25),
        ],
    },
}

_CATEGORY_PILLAR = {category: name for name, pillar in PILLARS.items()
                    for category in pillar['categories']}

RECENT_CATEGORY_WINDOW = 12


def pillar_of(entry):
    """The pillar a history entry belongs to, worked out from its shot
    category for posts made before pillars were recorded."""
    return entry.get("pillar") or _CATEGORY_PILLAR.get(entry.get("shot_category"))


def get_pillar(history):
    """The kind of post to make next, and the round it belongs to.

    Posts go in rounds of four, one of each kind in a random order - four posts
    is a week of the schedule. Weighting the draw towards whichever kind was
    falling behind still gave runs like spectacle, landmark, spectacle with no
    city at all; dealing from a deck can't. A new round never opens with the
    kind that closed the last one.
    """
    last = history[-1] if history else {}
    current = last.get("pillar_round")

    used = {entry.get("pillar") for entry in history
            if current is not None and entry.get("pillar_round") == current}
    remaining = [name for name in PILLARS if name not in used]

    if current is not None and remaining:
        return random.choice(remaining), current

    # Before rounds were recorded there's no round to finish, so one starts
    fresh = [name for name in PILLARS if name != pillar_of(last)]
    return random.choice(fresh), 0 if current is None else current + 1


CATEGORY_OPTION_COUNT = 3
LIGHT_OPTION_COUNT = 3
FRAMING_OPTION_COUNT = 3


def get_category_options(pillar, recent_categories=(), count=CATEGORY_OPTION_COUNT):
    """A shortlist of categories for the scout, preferring ones not used lately.

    Offered as a shortlist rather than imposed for the same reason as the light:
    a single category is often one the country has nothing good in, and the
    scout would rather fill it literally than substitute - abandoned places in
    the Netherlands came back as a disused runway in a field.
    """
    recent = set(recent_categories)
    fresh = [category for category in PILLARS[pillar]['categories'] if category not in recent]
    stale = [category for category in PILLARS[pillar]['categories'] if category in recent]
    random.shuffle(fresh)
    random.shuffle(stale)

    return (fresh + stale)[:count]


def match_category(name, options):
    """The shortlisted category the scout meant. It often drops the examples
    after the dash ("Wildlife Spectacles"), and the history only damps a
    category it can match exactly."""
    name = str(name or "").strip()
    for option in options:
        if name.lower() in (option.lower(), option.split(" - ")[0].lower()):
            return option

    return name or options[0]


def get_light_options(pillar, count=LIGHT_OPTION_COUNT):
    return random.sample(PILLARS[pillar]['light'], count)


def get_framing_options(pillar, count=FRAMING_OPTION_COUNT):
    return random.sample(PILLARS[pillar]['framings'], count)


def get_medium_look(pillar):
    return random.choice(PILLARS[pillar]['looks'])


def get_human_presence(pillar):
    presence = [option for option, _ in PILLARS[pillar]['people']]
    weights = [weight for _, weight in PILLARS[pillar]['people']]
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


def get_random_country(fileName, recent_countries=None, skip=()):
    with open(fileName, 'r') as file:
        countries = [line.strip() for line in file
                     if line.strip() and line.strip() not in skip]

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


def get_recent_categories(history, window=RECENT_CATEGORY_WINDOW):
    return [entry.get("shot_category") for entry in history[-window:]
            if entry.get("shot_category")]


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


def handle_image_generation(image_model, prompt, imageFileName, reference_path=None):
    generatedImageLink = image_model.generate_image(prompt, reference_path=reference_path)
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
