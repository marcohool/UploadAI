import json


def process_dalle_prompt_request(dalle_json_prompt):

    # Strip json markdown
    dalle_json_prompt = dalle_json_prompt.strip(
        '```json').replace("\n", "").replace("```", "")

    # Load JSON
    jsonPrompt = json.loads(dalle_json_prompt)

    locationGenerted = jsonPrompt["chosenLocation"]
    dallePrompt = jsonPrompt["promptValue"]

    return locationGenerted, dallePrompt
