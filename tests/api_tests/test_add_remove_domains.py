# tests/api_tests/test_add_remove_domains.py
import pytest
import requests
import json
import os
import re
from tests.api_tests import Aux_Library as aux

pytestmark = pytest.mark.order(5)

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

@pytest.mark.order(21)
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
    
# -------------------------------
# 2. Remove Domain Edge Cases (Planned Failure)
# -------------------------------
@pytest.mark.order(22)
def test_remove_domain_without_auth():
    """Removing a domain without authentication should fail."""
    BASE_URL = aux.BASE_URL
    resp = requests.post(
        f"{BASE_URL}/remove_domains",
        json={"domains": ["unauth.com"]},
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code in (401, 302, 403), f"Unexpected code: {resp.status_code}"

@pytest.mark.order(23)
def test_remove_nonexistent_domain(session_cookie):
    """Removing a non-existent domain should return a graceful error."""
    BASE_URL = aux.BASE_URL
    headers = {"Content-Type": "application/json", "Cookie": f"session={session_cookie}"}

    domain = "this-domain-does-not-exist.com"
    resp = requests.post(
        f"{BASE_URL}/remove_domains",
        json={"domains": [domain]},
        headers=headers,
    )
    assert resp.status_code in (200, 404)
    data = resp.json()
    assert "ok" in data

@pytest.mark.order(24)
def test_remove_domains_bulk(session_cookie):
    """Add several domains and remove them all in one API call."""
    BASE_URL = aux.BASE_URL
    headers = {"Content-Type": "application/json", "Cookie": f"session={session_cookie}"}

    domains = [f"bulk{i}.example.com" for i in range(3)]

    # Add all
    for d in domains:
        requests.post(f"{BASE_URL}/add_domain", json={"domain": d}, headers=headers)

    # Remove all at once
    rem_resp = requests.post(f"{BASE_URL}/remove_domains", json={"domains": domains}, headers=headers)
    assert rem_resp.status_code == 200, f"Bulk remove failed: {rem_resp.text}"
    assert rem_resp.json().get("ok") is True

    # Verify none remain
    list_resp = requests.get(f"{BASE_URL}/my_domains", headers=headers)
    assert list_resp.status_code == 200
    for d in domains:
        assert d not in str(list_resp.json()), f"{d} still present after bulk removal"

@pytest.mark.order(25)
def test_remove_domains_empty_payload(session_cookie):
    """Removing domains with empty payload should return 400 or ok:false."""
    BASE_URL = aux.BASE_URL
    headers = {"Content-Type": "application/json", "Cookie": f"session={session_cookie}"}

    resp = requests.post(f"{BASE_URL}/remove_domains", json={}, headers=headers)
    assert resp.status_code in (400, 422)
