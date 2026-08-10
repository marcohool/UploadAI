import os
import replicate

# Kept in config.json rather than here so the model and its inputs can be
# swapped without a code change - the two move together.
DEFAULT_INPUTS = {
    "aspect_ratio": "1:1",
    "output_format": "jpg",
    "safety_tolerance": 2,
}


class FluxModel:
    def __init__(self, model="black-forest-labs/flux-2-pro", inputs=None):
        self.client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))
        self.model = model
        self.inputs = DEFAULT_INPUTS if inputs is None else inputs

    def generate_image(self, prompt):
        try:
            output = self.client.run(
                self.model, input={"prompt": prompt, **self.inputs})
        except Exception as e:
            # Input schemas differ between model versions, and this runs
            # unattended twice a day - a rejected optional parameter shouldn't
            # cost the post. Retry with the prompt alone.
            if not self._is_input_error(e):
                raise

            print(f"Model rejected inputs {self.inputs} ({e}) - "
                  f"retrying with prompt only")
            output = self.client.run(self.model, input={"prompt": prompt})

        return self._extract_url(output)

    @staticmethod
    def _is_input_error(error):
        text = str(error).lower()
        return any(marker in text for marker in
                   ("422", "unprocessable", "invalid", "additional properties",
                    "not permitted", "unexpected", "schema", "input"))

    @staticmethod
    def _extract_url(output):
        if isinstance(output, list):
            output = output[0]

        if hasattr(output, "url"):
            return output.url

        return str(output)
