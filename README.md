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

Every push to `main` builds the image and publishes it to the GitHub Container Registry as `ghcr.io/marcohool/uploadai`, tagged `latest` and with the commit SHA. Images are built for `linux/amd64` and `linux/arm64`.

### Pull and run the published image
1. Pull the image:
```
docker pull ghcr.io/marcohool/uploadai:latest
```

2. Run the container:
```
docker run -d --name uploadai -v uploadai-data:/usr/src/app/data -e OPENAI_KEY=your_openai_key -e REPLICATE_API_TOKEN=your_replicate_api_token -e IG_UNAME=your_instagram_username -e IG_PWD=your_instagram_password ghcr.io/marcohool/uploadai:latest
```

If you already have a `.env` file, pass it directly instead of listing each variable:
```
docker run -d --name uploadai -v uploadai-data:/usr/src/app/data --env-file .env ghcr.io/marcohool/uploadai:latest
```

To pin a specific build rather than tracking `latest`, replace the tag with a commit SHA, e.g. `ghcr.io/marcohool/uploadai:f380a70...`.

The container runs on the built-in schedule and posts three times a day, so it is meant to stay running — hence `-d`. Follow its output with `docker logs -f uploadai`.

### Persisting state
The `-v uploadai-data:/usr/src/app/data` volume keeps `history.json` (so locations are never reused across restarts) and `session.json` (the saved Instagram login, which avoids re-authenticating every run). Without it, both are lost whenever the container is recreated.

Use a **named volume** as shown, not a bind mount to a host directory. Docker seeds an empty named volume from the image, so `config.json`, `prompts.json` and `countryList.txt` are preserved; a bind mount would hide them and the app would fail to start. Note that seeding only happens once — if a later image ships an updated `config.json` or `prompts.json`, the existing volume keeps the old copies. Remove the volume with `docker volume rm uploadai-data` to pick up the new defaults, at the cost of the post history.

### Building locally
```
docker build -t uploadai .
docker run -d --name uploadai -v uploadai-data:/usr/src/app/data --env-file .env uploadai
```

## Requirements
* OpenAI API key
* Replicate API token (for FLUX.2 [pro] image generation)
* Instagram account credentials
* Python 3.9+
* Required Python libraries (as listed in `requirements.txt`)
