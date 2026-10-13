# UploadAI
UploadAI is a Python application which automatically generates and posts AI-generated images to Instagram. It picks a spectacular place in a different country each time, generates a photorealistic image of it at its best, and uploads it with a caption built around one surprising, true fact about the place. The program runs four times a week.

Follow the page [here](https://www.instagram.com/worldswondersai/)!

* Leverages OpenAI's gpt-6-luna to scout locations, write image prompts and research and write captions, and Google's Nano Banana 2.1 (via Replicate) for photorealistic image creation. Nano Banana looks the place up with Google Search and Google Image Search before drawing it, so landmarks come out recognisable rather than as a generic version of their category. Both were chosen in blind tests against pricier options: Nano Banana 2.1 ranked best for accuracy and joint best for appeal against FLUX.2 [pro] and FLUX 3, and gpt-6-luna came close to gpt-5.5 at about 1/60th of the cost.
* Picks locations in two stages: the model proposes 12 candidate subjects and scores each for visual impact, and one of the top four is chosen at random. Asking for a single location just returns the country's most famous landmark almost every time; picking from all twelve lets the weakest ideas through.
* Every candidate has to be genuinely spectacular. The fame tier varies how well known the place is, never how good it looks: ~35% of posts are a country's world-famous wonders, ~45% are places just as striking that most people abroad have never heard of, ~20% are places famous within the country itself.
* Rotates between four kinds of post - nature, cities, landmarks and spectacles (festivals, wildlife migrations, shipwrecks, natural phenomena) - one of each in every four posts, in a random order and never the same kind twice running. Each kind has its own categories, light, compositions, renderings and people, so a city post looks like a city at night after rain rather than a deserted landscape at dawn.
* Samples the photographic parameters in Python rather than leaving them to the model - shot category, rendering and human presence are drawn independently. Composition and light are each offered as a shortlist of three, and the model picks whichever is a real vantage point and plausible for that place and season, so there's no snow in the tropics, aurora at the equator or mountain behind a landmark that can't be seen from there.
* Keeps a post history (`data/state/history.json`) so a location is never reused, recent subjects aren't repeated, and recently-used countries are damped down.
* Strips filler adjectives, editorial closing sentences and negation from generated prompts before they reach the image model.
* Researches facts about the place before writing the caption, and rewrites captions that contain numbers that weren't in the research, or that ask people to save, share, tag or comment (which stops Instagram recommending the post).
* Posts at 4:5 portrait (1080x1350) with a location line, five targeted hashtags (Instagram's cap) and alt text.
* Can post carousels: the cover plus more photographs of the same place - its most surprising view (Instagram re-shows a scrolled-past carousel from the second slide), a close detail and the place seen another way. The image model is shown the cover as a reference so every slide shows the same place. A slide that fails is left out rather than costing the post. Off by default to keep costs down - set `carousel_slides` in `config.json` (each extra slide adds about $0.034 a post).
* Automatically posts to Instagram using `instagrapi`.
* Geotags posts by geocoding the place with `geopy` and only accepting an Instagram location that's actually near it.
* Supports `--dry-run` to generate an image and caption locally without posting, for previewing output quality. `--output path/to/image.jpg` writes the image there, with a `.json` of everything that went into the post beside it.

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

### Automatic updates
The compose file also runs [Watchtower](https://github.com/nicholas-fedor/watchtower), which checks GHCR every 5 minutes and, when a new `latest` image has been published, pulls it, recreates the `uploadai` container and removes the old image. So a push to `main` reaches the running deployment within a few minutes of the build finishing, with no manual step. Only containers labelled `com.centurylinklabs.watchtower.enable=true` are touched. The image is public, so no registry login is needed on the host. Run `docker compose logs -f watchtower` to see update checks.

Common operations:
```
docker compose logs -f      # follow output
docker compose pull && docker compose up -d      # update immediately instead of waiting for Watchtower
docker compose down         # stop and remove the container
```

To pin a specific build instead of tracking `latest`, change the `image:` tag in `docker-compose.yml` to a commit SHA, e.g. `ghcr.io/marcohool/uploadai:f380a70...`. Watchtower then leaves it alone, since that tag never changes.

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
* Replicate API token (for Nano Banana 2.1 image generation - $0.0336 an image at 1K)
* Running cost: about $0.04 a post (~$0.70 a month at four posts a week) - the image is nearly all of it; text on gpt-6-luna is under a cent
* Instagram account credentials
* Python 3.9+
* Required Python libraries (as listed in `requirements.txt`)
