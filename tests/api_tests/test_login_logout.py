from .Aux_Library import check_login_user, check_logout_user
import pytest

pytestmark = pytest.mark.order(3)

@pytest.mark.parametrize("username,password", [
    ("JOHN_DOE", "PASSWORD"),        # case-sensitive mismatch
    ("john_doe", "wrong_password"),  # wrong password
    ("wrong_username", "password"),  # wrong username
    ("", "password"),                # empty username
    ("john_doe", ""),                # empty password
    ("", ""),                        # both empty
])
# Check invalid login scenarios
def test_1_login_invalid(username, password):
    login_response = check_login_user(username, password)
    assert login_response.status_code == 401 
    assert login_response.json().get("error") == "Invalid username or password"


# Check valid login
def test_2_login_valid_and_logout():
    login_response = check_login_user("john_doe", "password")
    session_cookie = login_response.cookies.get("session")
    assert login_response.status_code == 200 
    assert login_response.json().get("message") == "Login successful"
    assert login_response.json().get("username") == "john_doe"
    logout_response = check_logout_user(session_cookie)
    assert logout_response.status_code == 200 or logout_response.status_code == 302
    assert logout_response.cookies.get("session")== None
