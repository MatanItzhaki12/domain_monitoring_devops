import os
import requests
import re
import json
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)
from UserManagementModule import UserManager as UM
from IP_Library import FRONTEND_URL


# -----------------------------------------------------
# Global session and Base URL configuration
# -----------------------------------------------------
BASE_URL = FRONTEND_URL
session = requests.Session()


# -----------------------------------------------------
# Utility Functions
# -----------------------------------------------------

def extract_cookie(response):
    """
    Extract session cookie value from response headers.
    Returns the session token or None.
    """
    cookie_header = response.headers.get("Set-Cookie", "")
    match = re.search(r"session=([^;]+)", cookie_header)
    if match:
        return match.group(1)
    return None


def print_response(response):
    """
    Pretty print HTTP response info for debugging.
    """
    print(f"\n[{response.request.method}] {response.url}")
    print(f"Status: {response.status_code}")
    try:
        print("Response JSON:", json.dumps(response.json(), indent=2))
    except Exception:
        print("Response Text:", response.text[:300])
    print("-" * 60)


def assert_json_ok(response):
    """
    Helper assertion that response contains 'ok': True.
    """
    assert response.status_code == 200, f"Unexpected status: {response.status_code}"
    assert response.json().get("ok") is True, f"Response not ok: {response.text}"


# -----------------------------------------------------
# General HTTP helpers
# -----------------------------------------------------
def get(path: str, headers=None):
    """Wrapper for GET requests."""
    return session.get(f"{BASE_URL}{path}", headers=headers)


def post(path: str, data=None, json=None, headers=None, files=None):
    """Wrapper for POST requests."""
    return session.post(f"{BASE_URL}{path}", data=data, json=json, headers=headers, files=files)


# -----------------------------------------------------
# Webpage & Auth Endpoints
# -----------------------------------------------------
def check_get_webpage(path="/"):
    """Perform a simple GET request to verify server availability."""
    response = get(path)
    print_response(response)
    return response


def check_register_user(username, password, password_confirmation):
    """Register a new user."""
    payload = {
        "username": username,
        "password": password,
        "password_confirmation": password_confirmation
    }
    response = post("/register", json=payload)
    print_response(response)
    return response


def check_login_user(username, password):
    """Login existing user."""
    payload = {
        "username": username,
        "password": password
    }
    response = post("/login", json=payload)
    print_response(response)
    return response


def check_logout_user(cookie):
    """Logout the current user using their session cookie."""
    headers = {"Cookie": f"session={cookie}"}
    response = get("/logout", headers=headers)
    print_response(response)
    return response


def check_dashboard(cookie):
    """Access dashboard endpoint with session cookie."""
    headers = {"Cookie": f"session={cookie}"}
    response = get("/dashboard", headers=headers)
    print_response(response)
    return response


# -----------------------------------------------------
# Domain Management
# -----------------------------------------------------
def add_domain(domain, cookie):
    """Add a single domain for the logged-in user."""
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"session={cookie}"
    }
    payload = {"domain": domain}
    response = post("/add_domain", json=payload, headers=headers)
    print_response(response)
    return response


def remove_domains(domains, cookie):
    """Remove one or multiple domains."""
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"session={cookie}"
    }
    payload = {"domains": domains}
    response = post("/remove_domains", json=payload, headers=headers)
    print_response(response)
    return response


def list_domains(cookie):
    """Get the current user's domain list."""
    headers = {"Cookie": f"session={cookie}"}
    response = get("/my_domains", headers=headers)
    print_response(response)
    return response


def bulk_upload_domains(file_path, cookie):
    """Upload a .txt file with multiple domains."""
    headers = {"Cookie": f"session={cookie}"}
    with open(file_path, "rb") as f:
        response = post("/bulk_domains", files={"file": f}, headers=headers)
    print_response(response)
    return response


# -----------------------------------------------------
# Domain Monitoring
# -----------------------------------------------------

def check_scan_domains(session_cookie: str | None = None):
    """
    Performs a POST request to /scan_domains.
    """
    url = f"{BASE_URL}/scan_domains"
    cookies = {}

    if session_cookie:
        cookies["session"] = session_cookie

    # FIX: Changed from requests.get to requests.post
    response = requests.post(url, cookies=cookies, timeout=5)
    # Optional: print_response(response) if you want logs
    return response


# -----------------------------------------------------
# Removing existing user
# -----------------------------------------------------
def remove_user_from_running_app(username):
    # User Logout
    get("/logout")
    # Removing new test user
    UM().remove_user(username)
    # Reloading users.json to memory
    result = get("/reload_users_to_memory")
    return result
