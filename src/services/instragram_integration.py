from geopy.distance import distance
from instagrapi.exceptions import LoginRequired
from instagrapi import Client
from pathlib import Path
from utils.geo import geocode
import json
import os

# A place Instagram returns further than this from where the location actually
# geocodes to is a different place that happens to share a word with it.
MAX_PLACE_DISTANCE_KM = 75


def login_user():
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """
    cl = Client()
    session_path = Path("data/state/session.json")

    # A missing or empty session.json is normal on a fresh volume - fall
    # through to username/password login instead of aborting the whole run.
    try:
        session = cl.load_settings(session_path)
    except (FileNotFoundError, json.JSONDecodeError):
        session = None

    # dump_settings() writes without creating its parent directory, and on a
    # freshly mounted volume data/state doesn't exist until something writes
    # into it - history.json's writer makes its own directory, so this has to.
    session_path.parent.mkdir(parents=True, exist_ok=True)

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

            cl.dump_settings(session_path)
            return cl
        except Exception as e:
            print("Couldn't login user using session information: ", e)

    try:
        print(
            f"Attempting to login with username and password\n\tUsername: {os.getenv('IG_UNAME')}")
        if cl.login(os.getenv('IG_UNAME'), os.getenv('IG_PWD')):
            cl.dump_settings(session_path)
            return cl
    except Exception as e:
        print("Couldn't login user with username and password: ", e)

    raise Exception("Couldn't login user with either password or session")


def _is_match(place, query, coords):
    # Queries are "Place, Country"; Instagram usually names a place without
    # the country
    names = {query.strip().lower(), query.rsplit(",", 1)[0].strip().lower()}
    if place.name and place.name.strip().lower() in names:
        return True

    if place.lat is None or place.lng is None:
        return False

    return distance(coords, (place.lat, place.lng)).km <= MAX_PLACE_DISTANCE_KM


def find_location(cl, *queries):
    """Return the first place Instagram can find, trying each query in turn.

    fbsearch_places() searches around New York unless it's given coordinates,
    so an unfamiliar name used to come back as whatever Manhattan venue shared
    a word with it - a Thai village was tagged "East Village". Each query is
    geocoded first, searched around those coordinates, and a result is only
    accepted if it's actually near them. Falling back to a broader query beats
    tagging the wrong place.
    """
    for query in queries:
        if not query:
            continue

        coords = geocode(query)
        if not coords:
            print(f"Couldn't geocode {query!r}")
            continue

        try:
            places = cl.fbsearch_places(query, lat=coords[0], lng=coords[1])
        except Exception as e:
            print(f"Location search failed for {query!r}: ", e)
            continue

        for place in places:
            if _is_match(place, query, coords):
                print(f"Matched {query!r} -> {place}")
                return place

        print(f"No location match for {query!r} near {coords}")

    return None


def upload_photo(imagePath, caption, location, fallback_location=None, alt_text=None):
    cl = login_user()

    place = find_location(cl, location, fallback_location)

    extra_data = {"custom_accessibility_caption": alt_text} if alt_text else {}

    if place:
        cl.photo_upload(
            path=imagePath,
            caption=caption,
            location=place,
            extra_data=extra_data
        )
    else:
        cl.photo_upload(
            path=imagePath,
            caption=caption,
            extra_data=extra_data
        )

    print(f"Location photo uploaded with = {place}")
