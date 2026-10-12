import os
import time
import replicate

# Kept in config.json rather than here so the model and its inputs can be
# swapped without a code change - the two move together.
DEFAULT_INPUTS = {
    "aspect_ratio": "4:5",
    "resolution": "2 MP",
    "output_format": "jpg",
    "output_quality": 95,
    "safety_tolerance": 2,
}


class FluxModel:
    THROTTLE_RETRIES = 3
    THROTTLE_WAIT_SECONDS = 15

    def __init__(self, model="black-forest-labs/flux-2-pro", inputs=None):
        self.client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))
        self.model = model
        self.inputs = DEFAULT_INPUTS if inputs is None else inputs

    def _run(self, inputs):
        # Replicate throttles hard while the account balance is low (one
        # prediction at a time, six a minute). A throttled request is worth
        # waiting out - it's the same request a few seconds later.
        for attempt in range(self.THROTTLE_RETRIES + 1):
            try:
                return self.client.run(self.model, input=inputs)
            except Exception as e:
                if attempt == self.THROTTLE_RETRIES or not self._is_throttle(e):
                    raise

                print(f"Throttled by Replicate - retrying in "
                      f"{self.THROTTLE_WAIT_SECONDS}s")
                time.sleep(self.THROTTLE_WAIT_SECONDS)

    def generate_image(self, prompt):
        try:
            output = self._run({"prompt": prompt, **self.inputs})
        except Exception as e:
            # Input schemas differ between model versions, and this runs
            # unattended twice a day - a rejected optional parameter shouldn't
            # cost the post. Retry with the prompt alone.
            if not self._is_input_error(e):
                raise

            print(f"Model rejected inputs {self.inputs} ({e}) - "
                  f"retrying with prompt only")
            output = self._run({"prompt": prompt})

        return self._extract_url(output)

    @staticmethod
    def _is_throttle(error):
        text = str(error).lower()
        return "429" in text or "throttled" in text

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
