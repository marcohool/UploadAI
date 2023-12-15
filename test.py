import os
import urllib.request
from openai import OpenAI
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.types import Location
from pathlib import Path
from PIL import Image
import schedule
import random
import time
from geopy.geocoders import Nominatim


def main():
    print("arese")


geolocator = Nominatim(user_agent="get_lat_lng")
location = geolocator.geocode("Bulgaria country")
print(location)


if location:
    lat_lng = [location.latitude, location.longitude]
else:
    lat_lng = []
print(f"Lat_lng = {lat_lng}")
main()
