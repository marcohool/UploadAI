# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements.txt file into the container at /usr/src/app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code
COPY . .

# Set environment variables
ENV OPENAI_KEY your_openai_key
ENV IG_UNAME your_instagram_username
ENV IG_PWD your_instagram_password

# Run the script
CMD ["python", "./src/main.py"]
