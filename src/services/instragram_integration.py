from instagrapi.exceptions import LoginRequired
from instagrapi import Client
from pathlib import Path
import json
import os


def login_user():
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """
    cl = Client()

    # A missing or empty session.json is normal on a fresh volume - fall
    # through to username/password login instead of aborting the whole run.
    try:
        session = cl.load_settings(Path("data/session.json"))
    except (FileNotFoundError, json.JSONDecodeError):
        session = None

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


def find_location(cl, *queries):
    """Return the first place Instagram can find, trying each query in turn.

    Posts now favour obscure locations, so a search returning nothing - or
    fewer results than expected - is normal rather than exceptional. Falling
    back to a broader query beats losing the geotag or the whole upload.
    """
    for query in queries:
        if not query:
            continue

        try:
            places = cl.fbsearch_places(query)
        except Exception as e:
            print(f"Location search failed for {query!r}: ", e)
            continue

        if places:
            print(f"Matched {query!r} -> {places[0]}")
            return places[0]

        print(f"No location match for {query!r}")

    return None


def upload_photo(imagePath, caption, location, fallback_location=None):
    cl = login_user()

    place = find_location(cl, location, fallback_location)

    if place:
        cl.photo_upload(
            path=imagePath,
            caption=caption,
            location=place
        )
    else:
        cl.photo_upload(
            path=imagePath,
            caption=caption
        )

    print(f"Location photo uploaded with = {place}")
