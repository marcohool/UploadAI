from instagrapi.exceptions import LoginRequired
from instagrapi import Client
from pathlib import Path
import os


def login_user():
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """
    cl = Client()
    session = cl.load_settings(Path("data/session.json"))

    if session:
        try:
            cl.set_settings(session)
            cl.login(os.getenv('IG_UNAME'), os.getenv('IG_PWD'))

            # Check if session is valid
            try:
                cl.get_timeline_feed()
            except LoginRequired:
                print(
                    "Session invalid -> logging in with username and password")

                old_session = cl.get_settings()

                # Use the same device UUID
                cl.set_settings({})
                cl.set_settings(old_session["uuids"])

                cl.login(os.getenv('IG_UNAME'), os.getenv('IG_PWD'))

            cl.dump_settings(Path("data/session.json"))
            return cl
        except Exception as e:
            print("Couldn't login user using session information: ", e)

    try:
        print(
            f"Attempting to login with username and password\n\tUsername: {os.getenv('IG_UNAME')}")
        if cl.login(os.getenv('IG_UNAME'), os.getenv('IG_PWD')):
            cl.dump_settings(Path("data/session.json"))
            return cl
    except Exception as e:
        print("Couldn't login user with username and password: ", e)

    raise Exception("Couldn't login user with either password or session")


def upload_photo(imagePath, caption, location):
    cl = login_user()

    location = cl.fbsearch_places(location)[2]
    print(f"Location generated = {location}")

    if location:
        cl.photo_upload(
            path=imagePath,
            caption=caption,
            location=location
        )
    else:
        cl.photo_upload(
            path=location,
            caption=caption
        )

    print(f"Location photo uploaded with = {location}")
