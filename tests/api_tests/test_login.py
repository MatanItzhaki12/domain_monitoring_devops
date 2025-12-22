from .Aux_Library import check_login_user
import pytest

pytestmark = pytest.mark.order(3)

@pytest.mark.parametrize("username,password", [
    ("JOHN_DOE", "PASSWORD"),        # case-sensitive mismatch
    ("john_doe", "wrong_password"),  # wrong password
    ("wrong_username", "password"),  # wrong username
])

# Check invalid login scenarios
def test_1_login_invalid(username, password):
    login_response = check_login_user(username, password)
    assert login_response.status_code == 401 
    assert login_response.json().get("error") == "Invalid username or password"

@pytest.mark.parametrize("username,password", [
    ("", "password"),                # empty username
    ("john_doe", ""),                # empty password
    ("", ""),                        # both empty
])

def test_2_login_missing_fields(username, password):
    login_response = check_login_user(username, password)
    assert login_response.status_code == 400 
    assert login_response.json().get("error") == "username and password are required"


# Check valid login
def test_3_login_valid_and_logout():
    login_response = check_login_user("john_doe", "password")
    assert login_response.status_code == 200 
    assert login_response.json() == {"ok": True, "username": "john_doe"}


