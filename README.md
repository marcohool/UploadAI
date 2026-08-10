# UploadAI
UploadAI is a Python application which automatically generates and posts AI-generated images to Instagram. It creates unique image prompts, generates photorealistic images based on these prompts, and uploads them to Instagram with relevant captions and hashtags. The program is scheduled to run twice daily.

Follow the page [here](https://www.instagram.com/worldswondersai/)!

* Leverages OpenAI's GPT-4o to write prompts and captions, and FLUX.2 [pro] (via Replicate) for photorealistic image creation.
* Picks locations in two stages: the model proposes 12 candidate subjects spread across the country's regions, and one is chosen at random. Asking for a single location just returns the country's most famous landmark almost every time.
* Samples the photographic parameters in Python rather than leaving them to the model - shot category, fame tier, light, weather, lens and framing, film stock and human presence are drawn independently, giving a very large space of distinct looks.
* Weights location choice away from the obvious postcard shot: only ~10% of posts target a country's best-known international landmark, ~30% an entirely ordinary place.
* Keeps a post history (`data/history.json`) so a location is never reused, recent subjects aren't repeated, and recently-used countries are damped down.
* Strips filler adjectives, editorial closing sentences and negation from generated prompts before they reach the image model.
* Automatically posts to Instagram using `instagrapi`.
* Adds location tags to Instagram posts using `geopy`.
* Runs three times a day at specified times.
* Supports `--dry-run` to generate an image and caption locally without posting, for previewing output quality.

![image](https://github.com/marcohool/UploadAI/assets/64811388/436d6bbd-7545-4fa3-a915-32b2ae88e284)


## Installation§
* Clone the Repository: `git clone https://github.com/marcohool/UploadAI/`
* Install Dependencies: Run `pip install -r requirements.txt` to install necessary Python packages.
* Environment Setup: Create a `.env` file with your OpenAI API key, Replicate API token, Instagram username, and password (see `.env.sample`).
* Try it out without posting: `python src/main.py --dry-run`


## Docker 
This application can be containerized using Docker, ensuring an isolated and consistent environment.
1. Build the Docker Image:
```
docker build -t uploadai .
```

2. Run the Container:
```
docker run -e OPENAI_KEY=your_openai_key -e REPLICATE_API_TOKEN=your_replicate_api_token -e IG_UNAME=your_instagram_username -e IG_PWD=your_instagram_password uploadai
```

## Requirements
* OpenAI API key
* Replicate API token (for FLUX.2 [pro] image generation)
* Instagram account credentials
* Python 3.9+
* Required Python libraries (as listed in `requirements.txt`)
