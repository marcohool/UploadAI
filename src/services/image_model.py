import os
import time
import replicate

# Kept in config.json rather than here so the model and its inputs can be
# swapped without a code change - the two move together. Any image model on
# Replicate works, as long as its inputs are given to match.
DEFAULT_MODEL = "google/nano-banana-2.1"
DEFAULT_INPUTS = {
    "aspect_ratio": "4:5",
    "resolution": "1K",
    "google_search": True,
    "image_search": True,
    "output_format": "jpg",
}


class ImageModel:
    THROTTLE_RETRIES = 3
    THROTTLE_WAIT_SECONDS = 15

    def __init__(self, model=DEFAULT_MODEL, inputs=None, reference_input=None):
        self.client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))
        self.model = model
        self.inputs = DEFAULT_INPUTS if inputs is None else inputs
        # The input that takes reference images, for a model that should be
        # shown a carousel's cover so the later slides show the same place.
        # None for a model that shouldn't be given one.
        self.reference_input = reference_input

    def _run(self, inputs, reference_path=None):
        # Replicate throttles hard while the account balance is low (one
        # prediction at a time, six a minute). A throttled request is worth
        # waiting out - it's the same request a few seconds later.
        for attempt in range(self.THROTTLE_RETRIES + 1):
            try:
                if not reference_path:
                    return self.client.run(self.model, input=inputs)

                # Opened afresh on every attempt - a retry would otherwise
                # upload a file handle that's already been read to the end
                with open(reference_path, "rb") as reference:
                    return self.client.run(self.model, input={
                        **inputs, self.reference_input: [reference]})
            except Exception as e:
                if attempt == self.THROTTLE_RETRIES or not self._is_throttle(e):
                    raise

                print(f"Throttled by Replicate - retrying in "
                      f"{self.THROTTLE_WAIT_SECONDS}s")
                time.sleep(self.THROTTLE_WAIT_SECONDS)

    def generate_image(self, prompt, reference_path=None):
        if not self.reference_input:
            reference_path = None

        try:
            output = self._run({"prompt": prompt, **self.inputs}, reference_path)
        except Exception as e:
            # Input schemas differ between model versions, and this runs
            # unattended twice a day - a rejected optional parameter shouldn't
            # cost the post. Retry with the prompt alone. Not for a carousel
            # slide drawn from a reference, though: without the cover it comes
            # back as a different-looking place, and it's better left out.
            if reference_path or not self._is_input_error(e):
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
