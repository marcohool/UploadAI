import time

from geopy.geocoders import Nominatim

# Nominatim's usage policy allows one request a second
MIN_REQUEST_INTERVAL = 1.0

_last_request = 0.0


def geocode(query):
    """Coordinates for a place name, or None if it can't be found."""
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
