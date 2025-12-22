import os
import requests
import re
import json
from UserManagementModule import UserManager as UM

# -----------------------------------------------------
# Global session and Base URL configuration
# -----------------------------------------------------
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
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

def delete(path: str, json=None, headers=None):
    """Wrapper for DELETE requests."""
    return session.delete(f"{BASE_URL}{path}", json=json, headers=headers)


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
    response = post("/api/register", json=payload)
    print_response(response)
    return response


def check_login_user(username, password):
    """Login existing user. Returns response object."""
    payload = {
        "username": username,
        "password": password
    }
    response = post("/api/login", json=payload)
    print_response(response)
    return response


def check_dashboard(cookie):
    """Access dashboard endpoint with session cookie."""
    headers = {"Cookie": f"session={cookie}"}
    response = get("/dashboard", headers=headers)
    print_response(response)
    return response


# -----------------------------------------------------
# Domain Management (Backend API)
# -----------------------------------------------------

def add_domain(domain, username):
    """Add a single domain for the test user via Backend API."""
    # Backend expects X-Username header
    headers = {"X-Username": username}
    payload = {"domain": domain}
    
    # Path is /api/domains (POST)
    response = post("/api/domains", json=payload, headers=headers)
    print_response(response)
    return response


def remove_domains(domains_list, username):
    """
    Remove one or multiple domains via Backend API.
    Backend expects DELETE method on /api/domains with JSON body.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Username": username
    }
    payload = {"domains": domains_list}
    
    # Path is /api/domains (DELETE)
    response = delete("/api/domains", json=payload, headers=headers)
    print_response(response)
    return response


def list_domains(username):
    """Get the current user's domain list via Backend API."""
    headers = {"X-Username": username}
    
    # Path is /api/domains (GET)
    response = get("/api/domains", headers=headers)
    print_response(response)
    return response


def bulk_upload_domains(file_path, username):
    """Upload a .txt file with multiple domains via Backend API."""
    headers = {"X-Username": username}
    
    with open(file_path, "rb") as f:
        # Path is /api/domains/bulk (POST)
        response = post("/api/domains/bulk", files={"file": f}, headers=headers)
    
    print_response(response)
    return response


# -----------------------------------------------------
# Domain Monitoring
# -----------------------------------------------------

def check_scan_domains(username: str | None = None):
    """
    Performs a POST request to /api/scan.
    Backend requires X-Username header.
    """
    url = f"{BASE_URL}/api/scan"
    headers = {}

    if username:
        headers["X-Username"] = username

    # Note: Backend uses POST for scan
    response = requests.post(url, headers=headers, timeout=5)
    print_response(response)
    return response


# -----------------------------------------------------
# Removing existing user
# -----------------------------------------------------
def remove_user_from_running_app(username):
    # Removing new test user directly via UserManager
    UM().remove_user(username)
    # Reloading users.json to memory
    result = get("/reload_users_to_memory")
    return result