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
