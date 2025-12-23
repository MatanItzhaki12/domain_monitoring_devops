from tests.api_tests import Aux_Library
import pytest
import uuid

pytestmark = pytest.mark.order(6)

def test_1_scan_domains_unauthorized():
    """
    Calls /scan_domains with NO session cookie.
    Expected: 
    - 401 Unauthorized 
    - JSON response : {"ok": False, "error": "Unauthorized"}
    """
    response = Aux_Library.check_scan_domains(session_cookie=None)
    
    # FIX: Since we are now hitting the correct POST route, 
    # the app returns 401 Unauthorized (not 404 Not Found)
    assert response.status_code == 401

    data = response.json()
    assert data.get("ok") is False
    assert data.get("error") == "Unauthorized"


def test_2_scan_domains_authorized():
    """
    Full flow:
    - register user
    - Login
    - call "scan_domains" with session cookie
    - Check that the response is ok and has an 'updated' field.
    """
    username = f"scan_user_{uuid.uuid4().hex[:6]}"
    # Password must be 8-12 chars based on your backend rules
    password = "SafePass1" 

    # 1. Register
    reg_resp = Aux_Library.check_register_user(username, password, password)
    assert reg_resp.status_code in [200, 201]
    assert reg_resp.json().get("ok") is True

    # 2. Login
    login_resp = Aux_Library.check_login_user(username, password)
    assert login_resp.status_code == 200

    # 3. Extract Cookie using Aux Library
    session_cookie = Aux_Library.extract_cookie(login_resp)
    assert session_cookie is not None, "Failed to extract session cookie from login response"

    # 4. Scan
    scan_resp = Aux_Library.check_scan_domains(session_cookie=session_cookie)
    assert scan_resp.status_code == 200

    data = scan_resp.json()
    assert data.get("ok") is True, f"Expected ok=True, but got {data}"
    
    # Check for 'updated' key (returns int count of domains scanned)
    assert "updated" in data, f"'updated' key missing in response: {data}"
    assert isinstance(data["updated"], int)
    assert data["updated"] >= 0

    # 5. Cleanup
    Aux_Library.remove_user_from_running_app(username)