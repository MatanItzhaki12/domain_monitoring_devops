from tests.api_tests import Aux_Library
import sys
import os
import pytest
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app import app

pytestmark = pytest.mark.order(6)

def test_1_scan_domains_unauthorized():

    """
    Calls /scan_domains with NO session cookie.
    Expected: 
    -401 Unauthorized 
    -JSON response : {"ok": False, "error": "Unauthorized"}

    """
    response = Aux_Library.check_scan_domains()
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
    - Check that the response is ok and has an 'update' field that is INT and >=0.
    """

    username = f"test_scan_user_{uuid.uuid4().hex[:8]}"
    password = "StrongPass12"

    reg_resp = Aux_Library.check_register_user(
    username=username,
    password=password,
    password_confirmation=password,
                                                )
    assert reg_resp.ok == True

    login_resp = Aux_Library.check_login_user(
        username=username,
        password=password,
                                            )
    assert login_resp.status_code == 200

    #Extracting Flask session cookie
    session_cookie = login_resp.cookies.get("session")
    assert session_cookie is not None

    scan_resp = Aux_Library.check_scan_domains(session_cookie=session_cookie)
    assert scan_resp.status_code == 200

    data = scan_resp.json()

    assert data.get("ok") is True, f"Expected ok=True, but got {data}"
    assert "updated" in data, f"'updated' key missing in response: {data}"
    assert isinstance(data["updated"], int), f"'updated' must be int, but got {type(data['updated'])}"
    assert data["updated"] >= 0, f"'updated' must be >= 0, but got {data['updated']}"

    Aux_Library.remove_user_from_running_app(username=username)