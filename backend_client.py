import os
import requests
from flask import session
from IP_Library import BACKEND_URL
BACKEND_BASE_URL = BACKEND_URL

def backend_headers():
    headers = {}
    if "username" in session:
        headers["X-Username"] = session["username"]
    return headers


def _handle_response(response):
    try:
        data = response.json()
    except ValueError:
        data = {
            "ok": False,
            "error": "Invalid response from backend"
        }
    return data, response.status_code


def backend_get(path):
    return _handle_response(
        requests.get(
            f"{BACKEND_BASE_URL}{path}",
            headers=backend_headers(),
            timeout=10
        )
    )


def backend_post(path, **kwargs):
    return _handle_response(
        requests.post(
            f"{BACKEND_BASE_URL}{path}",
            headers=backend_headers(),
            timeout=10,
            **kwargs
        )
    )


def backend_delete(path, **kwargs):
    return _handle_response(
        requests.delete(
            f"{BACKEND_BASE_URL}{path}",
            headers=backend_headers(),
            timeout=10,
            **kwargs
        )
    )
