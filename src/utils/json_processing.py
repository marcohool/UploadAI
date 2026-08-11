import json
import re


def extract_json(raw_response):
    """Extract the first {...} JSON object, tolerating markdown code fences
    or any other surrounding text the model may add."""
    match = re.search(r'\{.*\}', raw_response, re.DOTALL)
    if not match:
        raise ValueError(
            f"No JSON object found in model response: {raw_response!r}")

    return json.loads(match.group(0))


def process_dalle_prompt_request(dalle_json_prompt):
    jsonPrompt = extract_json(dalle_json_prompt)

    locationGenerted = jsonPrompt["chosenLocation"]
    dallePrompt = jsonPrompt["promptValue"]

    return locationGenerted, dallePrompt


def process_location_candidates(candidates_json):
    """Return the list of {location, subject} candidates the scout proposed."""
    parsed = extract_json(candidates_json)

    candidates = parsed.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError(
            f"No candidates found in model response: {candidates_json!r}")

    valid = [candidate for candidate in candidates
             if isinstance(candidate, dict)
             and candidate.get("location") and candidate.get("subject")]

    if not valid:
        raise ValueError(
            f"No candidate had both a location and a subject: {candidates_json!r}")

    return valid


VALID_FACT_SCOPES = {"place", "region", "practice"}


def process_caption_facts(facts_json):
    """Return the researched [{fact, scope}] items the caption is built from.

    An empty list is a valid result rather than an error - the researcher is
    told to return nothing before it returns invented material, and the caption
    prompt handles having nothing to work with.
    """
    parsed = extract_json(facts_json)

    facts = parsed.get("facts")
    if not isinstance(facts, list):
        raise ValueError(f"No facts found in model response: {facts_json!r}")

    # An unrecognised scope is treated as the narrowest one, so a mislabelled
    # fact can't be presented as more widely true than it is
    return [{"fact": fact["fact"].strip(),
             "scope": fact.get("scope") if fact.get("scope") in VALID_FACT_SCOPES else "place"}
            for fact in facts
            if isinstance(fact, dict)
            and isinstance(fact.get("fact"), str) and fact["fact"].strip()]


def process_caption_response(caption_json):
    """Return the caption body and its hashtags as separate values."""
    parsed = extract_json(caption_json)

    caption = parsed.get("caption")
    if not isinstance(caption, str) or not caption.strip():
        raise ValueError(f"No caption found in model response: {caption_json!r}")

    hashtags = parsed.get("hashtags")
    if not isinstance(hashtags, list):
        hashtags = []

    return caption.strip(), [tag for tag in hashtags if isinstance(tag, str)]
