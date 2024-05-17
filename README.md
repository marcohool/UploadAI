# UploadAI
UploadAI is a Python application which automatically generates and posts AI-generated images to Instagram. It creates unique image prompts, generates images based on these prompts, and uploads them to Instagram with relevant captions and hashtags. The program is scheduled to run twice daily.

Follow the page [here](https://www.instagram.com/worldswondersai/)!

* Leverages OpenAI's GPT-4 for text generation and DALL-E 3 for image creation.
* Automatically posts to Instagram using `instagrapi`.
* Adds location tags to Instagram posts using `geopy`.
* Runs three times a day at specified times.

![image](https://github.com/marcohool/UploadAI/assets/64811388/436d6bbd-7545-4fa3-a915-32b2ae88e284)


## Installation
* Clone the Repository: `git clone https://github.com/marcohool/UploadAI/`
* Install Dependencies: Run `pip install -r requirements.txt` to install necessary Python packages.
* Environment Setup: Create a `.env` file with your OpenAI API key, Instagram username, and password.


## Docker 
This application can be containerized using Docker, ensuring an isolated and consistent environment.
1. Build the Docker Image:
```
docker build -t uploadai .
```

2. Run the Container:
```
docker run -e OPENAI_KEY=your_openai_key -e IG_UNAME=your_instagram_username -e IG_PWD=your_instagram_password uploadai
```

## Requirements
* OpenAI API key
* Instagram account credentials
* Python 3.9+
* Required Python libraries (as listed in `requirements.txt`)
