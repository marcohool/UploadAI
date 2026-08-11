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

### Running with Docker Compose
Clone the repository, create a `.env` file (see `.env.sample`), then:
```
docker compose up -d
```

That pulls the published image, loads credentials from `.env`, and restarts the app automatically unless you stop it yourself. Cloning the repository is only needed to get `docker-compose.yml` and `.env.sample` - the app itself runs from the published image and doesn't read from your working tree.

Common operations:
```
docker compose logs -f      # follow output
docker compose pull && docker compose up -d      # update to the latest image
docker compose down         # stop and remove the container
```

To pin a specific build instead of tracking `latest`, change the `image:` tag in `docker-compose.yml` to a commit SHA, e.g. `ghcr.io/marcohool/uploadai:f380a70...`.

### State and configuration
`config.json`, `prompts.json` and `countryList.txt` ship baked into the image at `data/`, so the container is self-contained and doesn't need a local `./data` folder to run. `history.json` (which keeps locations from being reused) and `session.json` (the saved Instagram login, which avoids re-authenticating every run) are the only things that need to persist, so they live under `data/state/`, which is mounted as a single named Docker volume (`state`) that survives restarts and image updates.

To change `config.json`, `prompts.json` or `countryList.txt`, edit them in the repo and rebuild/re-pull the image - editing a local copy no longer has any effect on a running container. To inspect or reset the persisted state, use `docker compose exec uploadai cat data/state/history.json` or `docker compose down -v` to drop it and start clean.

**Upgrading an existing deployment:** older versions bind-mounted `./data` directly and kept `history.json`/`session.json` at its top level. Before switching to the new `docker-compose.yml`, move your existing state into place so it isn't lost: `mkdir -p data/state && mv data/history.json data/session.json data/state/`, then `docker compose up -d`.

### Building locally
To run your working tree instead of the published image, add a `build: .` line to the service in `docker-compose.yml` and use:
```
docker compose up -d --build
```

## Requirements
* OpenAI API key
* Replicate API token (for FLUX.2 [pro] image generation)
* Instagram account credentials
* Python 3.9+
* Required Python libraries (as listed in `requirements.txt`)
