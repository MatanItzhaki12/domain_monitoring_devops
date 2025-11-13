# tests/api_tests/test_add_remove_domains.py
import pytest
import requests
import json
import os
import re
import Aux_Library as aux


def load_test_user():
    """
    Load user from users.json.
    Fallback to default user if not found.
    """
    users_file = os.path.join(os.path.dirname(__file__), "..", "..", "UsersData", "users.json")
    if os.path.exists(users_file):
        with open(users_file, "r", encoding="utf-8") as f:
            users = json.load(f)
        if isinstance(users, list) and len(users) > 0:
            return users[0]
    return {"username": "apitester", "password": "Apitester1"}


@pytest.fixture(scope="session")
def session_cookie():
    """
    Logs in using Aux_Library.check_login_user and extracts the session cookie.
    """
    user = load_test_user()
    response = aux.check_login_user(user["username"], user["password"])
    assert response.status_code == 200, f"Login failed: {response.text}"
    assert response.json().get("ok"), f"Unexpected login response: {response.text}"

    # Extract the session cookie
    cookie_header = response.headers.get("Set-Cookie", "")
    match = re.search(r"session=([^;]+)", cookie_header)
    assert match, "Session cookie not found in login response"
    cookie = match.group(1)
    print(f"[INFO] Logged in as {user['username']}, session cookie: {cookie[:12]}...")
    return cookie


def test_add_and_remove_domain(session_cookie):
    """
    Full add/remove domain test:
    1. Add domain via /add_domain
    2. Verify it appears in /my_domains
    3. Remove it via /remove_domains
    4. Confirm it is gone
    """
    BASE_URL = aux.BASE_URL  # Use from Aux_Library
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"session={session_cookie}"
    }

    test_domain = "pytest-example.com"

    # Add domain
    add_resp = requests.post(f"{BASE_URL}/add_domain", json={"domain": test_domain}, headers=headers)
    print(f"[ADD_DOMAIN] {add_resp.status_code} - {add_resp.text}")
    assert add_resp.status_code in (201, 409)
    assert "ok" in add_resp.json()

    # Verify domain list
    list_resp = requests.get(f"{BASE_URL}/my_domains", headers=headers)
    print(f"[MY_DOMAINS] {list_resp.status_code} - {list_resp.text}")
    assert list_resp.status_code == 200
    data = list_resp.json().get("data", [])
    assert any(test_domain in str(d) for d in data), "Domain not found after add_domain"

    # Remove domain
    remove_resp = requests.post(f"{BASE_URL}/remove_domains", json={"domains": [test_domain]}, headers=headers)
    print(f"[REMOVE_DOMAIN] {remove_resp.status_code} - {remove_resp.text}")
    assert remove_resp.status_code == 200
    assert remove_resp.json().get("ok") is True

    # Confirm removal
    verify_resp = requests.get(f"{BASE_URL}/my_domains", headers=headers)
    print(f"[VERIFY_REMOVAL] {verify_resp.status_code} - {verify_resp.text}")
    domains_after = verify_resp.json().get("data", [])
    assert not any(test_domain in str(d) for d in domains_after), "Domain still present after removal"

    print("Add/remove domain test completed successfully.")
