import pytest
import uuid
from tests.api_tests import Aux_Library as aux

pytestmark = pytest.mark.order(6)

def test_1_scan_domains_unauthorized():
    """
    Calls /api/scan without X-Username header.
    Expected: 
    - 401 Unauthorized 
    - JSON response : {"ok": False, "error": "Unauthorized"}
    """
    # Passing None means no X-Username header
    response = aux.check_scan_domains(username=None)
    
    assert response.status_code == 401
    data = response.json()
    assert data.get("ok") is False
    assert data.get("error") == "Unauthorized"


def test_2_scan_domains_authorized():
    """
    Full flow:
    - Register user (so they exist in Backend User Manager)
    - Call "/api/scan" with X-Username header
    - Check that the response is ok and has an 'updated' field >= 0
    """
    # 1. Setup unique user
    username = f"test_scan_{uuid.uuid4().hex[:8]}"
    password = "StrongPass12"

    # Register to ensure user exists in the backend system
    reg_resp = aux.check_register_user(
        username=username,
        password=password,
        password_confirmation=password
    )
    assert reg_resp.status_code == 201
    assert reg_resp.json().get("ok") is True

    try:
        # 2. Call Scan (No login needed for backend API, just username header)
        scan_resp = aux.check_scan_domains(username=username)
        
        # 3. Validation
        assert scan_resp.status_code == 200
        data = scan_resp.json()

        assert data.get("ok") is True, f"Expected ok=True, but got {data}"
        assert "updated" in data, f"'updated' key missing in response: {data}"
        assert isinstance(data["updated"], int), f"'updated' must be int, but got {type(data['updated'])}"
        assert data["updated"] >= 0, f"'updated' must be >= 0, but got {data['updated']}"
        
        print(f"\n[INFO] Scan successful for {username}. Updated count: {data['updated']}")

    finally:
        # 4. Cleanup
        aux.remove_user_from_running_app(username=username)