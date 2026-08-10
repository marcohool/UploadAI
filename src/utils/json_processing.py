import json
import re


def process_dalle_prompt_request(dalle_json_prompt):

    # Extract the first {...} JSON object, tolerating markdown code fences
    # or any other surrounding text the model may add.
    match = re.search(r'\{.*\}', dalle_json_prompt, re.DOTALL)
    if not match:
        raise ValueError(
            f"No JSON object found in model response: {dalle_json_prompt!r}")

    jsonPrompt = json.loads(match.group(0))

    locationGenerted = jsonPrompt["chosenLocation"]
    dallePrompt = jsonPrompt["promptValue"]

    return locationGenerted, dallePrompt
