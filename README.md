# UploadAI
UploadAI is a Python application which automatically generates and posts AI-generated images to Instagram. It creates unique image prompts, generates photorealistic images based on these prompts, and uploads them to Instagram with relevant captions and hashtags. The program is scheduled to run twice daily.

Follow the page [here](https://www.instagram.com/worldswondersai/)!

* Leverages OpenAI's GPT-4o to write prompts and captions, and Flux 1.1 Pro (via Replicate) for photorealistic image creation.
* Draws from a list of ~174 countries and a set of shot categories (cityscape, small town, nature, mountains, beach, wildlife, countryside, cultural sites, food/markets, people & culture) so posts don't repeat the same kind of shot.
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
* Replicate API token (for Flux 1.1 Pro image generation)
* Instagram account credentials
* Python 3.9+
* Required Python libraries (as listed in `requirements.txt`)
