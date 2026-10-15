"""Small HTTP helper for the Frankfurter API."""

import requests


def get_url(url: str) -> tuple[int, str]:
    """Return an HTTP status code and response text for a GET request.

    A network failure has no HTTP response, so it is reported with status 0.
    Keeping that case in the return value lets the caller show a useful error
    without crashing the Streamlit app.
    """
    try:
        response = requests.get(url, timeout=15)
    except requests.RequestException as exc:
        return 0, str(exc)
    return response.status_code, response.text
