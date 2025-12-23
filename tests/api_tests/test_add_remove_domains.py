import pytest
import uuid
from tests.api_tests import Aux_Library as aux

# Ensure tests run in specific order if configured
pytestmark = pytest.mark.order(5)

@pytest.fixture(scope="module")
def user_session():
    """
    Fixture to setup a test user:
    1. Registers a new user.
    2. Logs them in.
    3. Extracts and returns the session cookie.
    4. Teardown: Removes user from DB.
    """
    # 1. Generate unique credentials
    username = f"fe_test_{uuid.uuid4().hex[:8]}"
    
    # FIX: Password must be 8-12 characters long
    password = "TestPass12" 

    # 2. Register
    reg_resp = aux.check_register_user(username, password, password)
    assert reg_resp.status_code in [200, 201], f"Registration failed: {reg_resp.text}"

    # 3. Login
    login_resp = aux.check_login_user(username, password)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"

    # 4. Extract Session Cookie
    cookie = aux.extract_cookie(login_resp)
    assert cookie, "Login succeeded but no 'session' cookie found in headers."
    
    print(f"\n[INFO] Authenticated as {username} with session: {cookie[:10]}...")
    
    yield cookie

    # 5. Cleanup
    aux.remove_user_from_running_app(username)


def test_1_add_and_remove_single_domain(user_session):
    """
    Verifies adding and removing a single domain using Session Cookie.
    """
    cookie = user_session
    domain = f"test-single-{uuid.uuid4().hex[:4]}.com"

    # 1. Add Domain
    add_resp = aux.add_domain(domain, cookie)
    assert add_resp.status_code in [200, 201]
    assert add_resp.json().get("ok") is True

    # 2. Verify Domain exists (using Dashboard since /my_domains isn't in app.py)
    dash_resp = aux.check_dashboard(cookie)
    assert dash_resp.status_code == 200
    assert domain in dash_resp.text, f"Domain {domain} not found in dashboard HTML"

    # 3. Remove Domain
    # Frontend remove_domains route expects a list of domains
    remove_resp = aux.remove_domains([domain], cookie)
    assert remove_resp.status_code == 200
    assert remove_resp.json().get("ok") is True

    # 4. Verify Removal
    dash_resp_after = aux.check_dashboard(cookie)
    assert domain not in dash_resp_after.text, f"Domain {domain} still present after removal"


def test_2_remove_domain_unauthorized():
    """
    Verifies that removing a domain without a valid session cookie fails.
    """
    # Pass None as cookie
    resp = aux.remove_domains(["unauth.com"], cookie=None)
    
    # Frontend app.py returns 401 if "username" not in session
    assert resp.status_code == 401
    assert resp.json().get("error") == "Unauthorized"


def test_3_add_remove_bulk_domains(user_session):
    """
    Verifies bulk adding and removing of domains.
    """
    cookie = user_session
    domains = [f"bulk-{i}-{uuid.uuid4().hex[:4]}.com" for i in range(3)]

    # 1. Add multiple domains
    for d in domains:
        resp = aux.add_domain(d, cookie)
        assert resp.status_code in [200, 201]

    # 2. Verify all are present in Dashboard
    dash_resp = aux.check_dashboard(cookie)
    for d in domains:
        assert d in dash_resp.text, f"Bulk domain {d} missing from dashboard"

    # 3. Remove all at once
    rem_resp = aux.remove_domains(domains, cookie)
    assert rem_resp.status_code == 200
    assert rem_resp.json().get("ok") is True

    # 4. Verify dashboard is clear of these domains
    dash_resp_after = aux.check_dashboard(cookie)
    for d in domains:
        assert d not in dash_resp_after.text, f"Bulk domain {d} still present after removal"


def test_4_remove_nonexistent_domain(user_session):
    """
    Verifies that removing a domain that doesn't exist is handled gracefully.
    """
    cookie = user_session
    fake_domain = "nonexistent-domain.com"

    resp = aux.remove_domains([fake_domain], cookie)
    
    # Should return 200 OK (idempotent behavior is standard for this app)
    assert resp.status_code == 200
    assert resp.json().get("ok") is True

def test_5_remove_domains_empty_payload(user_session):
    """
    Verifies that sending an empty list to remove_domains returns a success or error
    depending on implementation (app.py simply passes it to backend).
    """
    cookie = user_session
    
    # Passing empty list
    resp = aux.remove_domains([], cookie)
    
    # Backend usually validates this. Expecting 400 Bad Request if validation exists.
    assert resp.status_code in [400, 422]