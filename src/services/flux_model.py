import os
import replicate


class FluxModel:
    def __init__(self, model="black-forest-labs/flux-1.1-pro"):
        self.client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))
        self.model = model

    def generate_image(self, prompt):
        output = self.client.run(
            self.model,
            input={
                "prompt": prompt,
                "aspect_ratio": "1:1",
                "output_format": "jpg",
                "safety_tolerance": 2,
                "prompt_upsampling": False,
            },
        )

        return self._extract_url(output)

    @staticmethod
    def _extract_url(output):
        if isinstance(output, list):
            output = output[0]

        if hasattr(output, "url"):
            return output.url

        return str(output)
