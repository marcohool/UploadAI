import time

from geopy.geocoders import Nominatim

# Nominatim's usage policy allows one request a second
MIN_REQUEST_INTERVAL = 1.0

_last_request = 0.0


def _lookup(query):
    global _last_request

    wait = MIN_REQUEST_INTERVAL - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()

    try:
        result = Nominatim(user_agent="uploadai").geocode(query, timeout=10)
    except Exception as e:
        print(f"Geocoding failed for {query!r}: ", e)
        return None

    return (result.latitude, result.longitude) if result else None


def geocode(query):
    """Coordinates for a place name, or None if it can't be found.

    Locations are written "Place, Country", and some country names in
    countryList.txt aren't ones OpenStreetMap knows ("Sistine Chapel, Holy See"
    finds nothing; "Sistine Chapel" does), so the place is tried on its own
    when the full name fails.
    """
    coords = _lookup(query)

    if coords is None and "," in query:
        coords = _lookup(query.rsplit(",", 1)[0].strip())

    return coords
