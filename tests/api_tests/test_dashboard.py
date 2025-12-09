# tests/api_tests/test_dashboard.py
import json, os, time, requests, pytest
from tests.api_tests.Aux_Library import (
    BASE_URL,
    check_dashboard,
    check_register_user,
    check_login_user,
)
from app import app

pytestmark = pytest.mark.order(4)

# ============================================================
# Utilities
# ============================================================

def cleanup_user(username: str):
    """Remove only the test user and its domain file."""
    users_path = os.path.join("UsersData", "users.json")
    domains_path = os.path.join("UsersData", f"{username}_domains.json")

    if os.path.exists(users_path):
        with open(users_path, "r+", encoding="utf-8") as f:
            try:
                users = json.load(f)
            except json.JSONDecodeError:
                users = []

            for i, u in enumerate(users):
                if u.get("username") == username:
                    users.pop(i)
                    f.seek(0)
                    json.dump(users, f, indent=4)
                    f.truncate()
                    break

    if os.path.exists(domains_path):
        os.remove(domains_path)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="session")
def client():
    """Provide an in-process Flask test client (used for unauthenticated checks)."""
    with app.test_client() as c:
        yield c


@pytest.fixture(scope="session")
def test_session_cookie():
    """Create one test user and share its session cookie for all authenticated dashboard tests."""
    username = f"pytest_shared_{int(time.time())}"
    password = "Test1234"

    check_register_user(username, password, password)
    cookie = check_login_user(username, password).cookies.get("session")
    assert cookie, "Failed to obtain session cookie for shared user"

    try:
        yield cookie
    finally:
        cleanup_user(username)


# ============================================================
# Dashboard Tests
# ============================================================

# -------------------------------
# 1. Access Control & Auth Tests
# -------------------------------
def test_1_dashboard_redirect_when_not_logged_in(client):
    """Unauthenticated users should be redirected to login."""
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code in [302, 401, 200]
    if r.status_code == 302:
        assert "login" in r.location.lower()
    else:
        assert "login" in r.data.decode().lower()

def test_2_dashboard_invalid_cookie_redirects(client):
    """Invalid session cookie should redirect to login."""
    r = client.get("/dashboard", headers={"Cookie": "session=invalid_cookie"}, follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in (r.location or "").lower()

def test_3_dashboard_access(test_session_cookie):
    """Authenticated user can access dashboard via real HTTP."""
    r = requests.get(
        f"{BASE_URL}/dashboard",
        headers={"Cookie": f"session={test_session_cookie}"}
    )
    assert r.status_code == 200, f"Unexpected {r.status_code}: {r.text}"
    assert "domain monitoring system" in r.text.lower()


# -------------------------------
# 2. Dashboard Content Validation
# -------------------------------
def test_4_dashboard_greeting_shows_username(test_session_cookie):
    """Dashboard should greet the logged-in user by name."""
    r = requests.get(
        f"{BASE_URL}/dashboard",
        headers={"Cookie": f"session={test_session_cookie}"}
    )
    assert r.status_code == 200
    body = r.text.lower()
    assert "hello" in body and "pytest_shared" in body, "Greeting or username missing on dashboard."

def test_5_dashboard_shows_empty_state_for_new_user(test_session_cookie):
    """Authenticated user with no domains should see 'No domains added yet' message."""
    r = requests.get(
        f"{BASE_URL}/dashboard",
        headers={"Cookie": f"session={test_session_cookie}"}
    )
    assert r.status_code == 200
    body = r.text.lower()
    assert "no domains added yet" in body or "use the buttons above" in body

def test_6_dashboard_static_assets_load():
    """Dashboard static CSS and JS should be accessible and non-empty."""
    assets = [
        "/static/dashboard/dashboard.css",
        "/static/dashboard/dashboard.js",
    ]

    for path in assets:
        r = requests.get(f"{BASE_URL}{path}")
        assert r.status_code == 200, f"Static asset missing or not served correctly: {path}"
        assert len(r.text.strip()) > 0, f"Static asset {path} appears empty or corrupted"



# -------------------------------
# 3. Dynamic Content Behavior
# -------------------------------
def test_7_dashboard_reflects_domain_add_remove(test_session_cookie):
    """Verify dashboard updates after adding and removing a domain."""
    test_domain = f"test{int(time.time())}.com"

    # Add domain via API
    add_resp = requests.post(
        f"{BASE_URL}/add_domain",
        json={"domain": test_domain},
        headers={
            "Cookie": f"session={test_session_cookie}",
            "Content-Type": "application/json"
        },
    )
    assert add_resp.status_code in (201, 409), f"Add domain failed: {add_resp.text}"

    # Dashboard should show domain
    r = requests.get(
        f"{BASE_URL}/dashboard",
        headers={"Cookie": f"session={test_session_cookie}"}
    )
    assert r.status_code == 200
    assert test_domain in r.text, f"{test_domain} not found on dashboard"

    # Remove domain via API
    rem_resp = requests.post(
        f"{BASE_URL}/remove_domains",
        json={"domains": [test_domain]},
        headers={
            "Cookie": f"session={test_session_cookie}",
            "Content-Type": "application/json"
        },
    )
    assert rem_resp.status_code == 200, f"Remove failed: {rem_resp.text}"

    # Dashboard should not show domain
    r2 = requests.get(
        f"{BASE_URL}/dashboard",
        headers={"Cookie": f"session={test_session_cookie}"}
    )
    assert r2.status_code == 200
    assert test_domain not in r2.text, f"{test_domain} still present after removal"
