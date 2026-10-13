import os

from utils.data_helpers import alt_text, handle_image_generation
from utils.json_processing import extract_json
from utils.prompt_cleanup import clean_image_prompt

# Carousels reach further than single photos: Instagram re-shows one that was
# scrolled past starting from its second slide, and swiping is time spent on
# the post. Every slide after the cover is another photograph of the same
# place, so the slides have to agree with each other.

# Drawn from separate prompts alone, a lesser-known place comes out looking
# different on every slide, so the image model is shown the cover as a
# reference. Some models (FLUX.2) then copy its framing unless pushed away from
# it - an early slide 2 came back as the cover with a few pilgrims added.
REFERENCE_NOTE = (
    "The image model will be given the cover photograph as a reference image so "
    "it can keep the place consistent. Begin every prompt with \"The same place "
    "as in the reference photo,\" and then describe the new view in full - what "
    "the camera sees from where it now stands, and the light. Given a reference, "
    "the image model copies its framing unless told exactly where the camera has "
    "moved to, so open each description with a camera position clearly different "
    "from the cover's - much closer, from the far side, from above at an angle, or "
    "from inside.")

# For a model without a reference input configured. Some models (FLUX 3) are
# better without one: given a reference they switch to editing it, and the
# "new" slide comes back as the cover with something added to it.
GROUNDED_NOTE = (
    "The image model looks the named place up before it draws, so begin every "
    "prompt by naming the place exactly as given.")


def slide_path(cover_path, number):
    root, ext = os.path.splitext(cover_path)
    return f"{root}_{number}{ext}"


def plan_slides(text_model, prompts, *, location, hero_prompt, count, uses_reference):
    """Image prompts for the slides that follow the cover."""
    raw = text_model.get_text_response(1.0, prompts['carousel_slides_prompt'].format(
        chosenLocation=location, heroPrompt=hero_prompt, slideCount=count,
        referenceNote=REFERENCE_NOTE if uses_reference else GROUNDED_NOTE))

    slides = extract_json(raw).get("slides")
    if not isinstance(slides, list):
        raise ValueError(f"No slides found in model response: {raw!r}")

    return [slide for slide in slides
            if isinstance(slide, dict)
            and isinstance(slide.get("promptValue"), str)
            and slide["promptValue"].strip()][:count]


def build_carousel(text_model, prompts, image_model, *, location, country,
                   hero_prompt, cover_path, count):
    """Generate the slides after the cover, returning those that worked.

    A slide that fails is left out rather than failing the post - a carousel
    of three, or the cover on its own, still beats no post at all.
    """
    if count < 1:
        return []

    uses_reference = bool(image_model.reference_input)

    try:
        planned = plan_slides(text_model, prompts, location=location,
                              hero_prompt=hero_prompt, count=count,
                              uses_reference=uses_reference)
    except Exception as e:
        print("Couldn't plan carousel slides, posting the cover alone: ", e)
        return []

    slides = []
    for slide in planned:
        path = slide_path(cover_path, len(slides) + 2)
        prompt = clean_image_prompt(slide["promptValue"])
        print(f"Got slide {len(slides) + 2} ({slide.get('shot', '')}) -> ", prompt)

        try:
            handle_image_generation(image_model, prompt, path,
                                    reference_path=cover_path if uses_reference else None)
            slides.append({
                "path": path,
                "shot": str(slide.get("shot") or ""),
                "prompt": prompt,
                "alt": alt_text(str(slide.get("altText") or slide.get("shot") or location),
                                location, country),
            })
        except Exception as e:
            print(f"Couldn't generate slide {len(slides) + 2}, leaving it out: ", e)

    return slides
