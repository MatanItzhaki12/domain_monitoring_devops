import pytest, time
from tests.selenium_tests.pages.register_page import RegisterPage
from tests.selenium_tests.pages.dashboard_page import DashboardPage
from tests.api_tests.Aux_Library import remove_user_from_running_app as rm_user

pytestmark = pytest.mark.order(7)

EXISTING_USERNAME = "test1"
NEW_USERNAME = "test31"

# Fixtures

@pytest.fixture
def clean_user():
    users_cleanup_list = []

    def _cleanup_user(username):
        users_cleanup_list.append(username)
        # # Remove user, if exist
        # rm_user(username)

    # This let the test tell which user to clean
    yield _cleanup_user

    # Removing every user in the list at the end of the test
    for user in users_cleanup_list:
        # Cleanup - Remove User
        rm_user(username=user)            

# Tests

@pytest.mark.order(21)
def test_click_here_to_login(driver, base_url):
    # Initializing and Loading Register Page
    register = RegisterPage(driver, base_url)
    register.load()
    # Registering a Given Set of Credentials
    register.move_to_login_page()
    # After Failed Attempt, The Driver Should be in Register Page
    assert register.get_title() == "Login"

@pytest.mark.order(22)
@pytest.mark.parametrize(
        "username,password,password_confirmation,expected_message",
        [
            # Invalid username
            ("", "Qwe12345", "Qwe12345","Username invalid."),
            # Existing username
            (EXISTING_USERNAME, "Qwe12345", "Qwe12345", "Username already taken."),
            # Invalid password confirmation
            (NEW_USERNAME, "Qwe12345", "Qwe12346", "Password and Password Confirmation are not the same."),
            # password not long enough - less than 8 characters
            (NEW_USERNAME, "Qwe1234", "Qwe1234", "Password is not between 8 to 12 characters."),
            # password too long - more than 12 characters
            (NEW_USERNAME, "Qwe1234567890", "Qwe1234567890", "Password is not between 8 to 12 characters."),
            # password does not include at least one uppercase character
            (NEW_USERNAME, "qwe12345", "qwe12345", "Password does not include at least one uppercase character."),
            # password does not include at least one lowercase character
            (NEW_USERNAME, "QWE12345", "QWE12345", "Password does not include at least one lowercase character."),
            # password does not include at least one digits
            (NEW_USERNAME, "Qwertyuiop", "Qwertyuiop", "Password does not include at least one digit."),
            # password include characters that are not uppercase, lowercase or digits
            (NEW_USERNAME, "Qwe12345!", "Qwe12345!", "Password should include only uppercase characters, lowercase characters and digits!")
        ]
)
def test_Invalid_registration(driver, base_url, username, password, 
                              password_confirmation, expected_message):
    # Initializing and Loading Register Page
    register = RegisterPage(driver, base_url)
    register.load()
    # Registering a Given Set of Credentials
    register.register(
        username=username,
        password=password,
        password_confirmation=password_confirmation
        )
    # After Failed Attempt, The Driver Should be in Register Page
    assert register.get_title() == "Register"
    # Check The Correctness of Error Message
    assert register.get_error_message() == expected_message
    ##assert dashboard.get_welcome_message() == f"Hello {username}!"

@pytest.mark.order(23)
@pytest.mark.parametrize(
        "username,password,password_confirmation,expected_message",
        [
            (NEW_USERNAME, "Qwe12345", "Qwe12345", "Registered Successfully.")
        ]
)
def test_valid_registration(driver, base_url, clean_user, username, password, 
                            password_confirmation, expected_message):
    # Adding user to cleanup list
    clean_user(username)
    # Initializing and Loading Register Page
    register = RegisterPage(driver, base_url)
    register.load()
    # Registering a Given Set of Credentials
    register.register(
        username=username,
        password=password,
        password_confirmation=password_confirmation
        )
    # Check The Correctness of Error Message
    assert register.get_success_message() == expected_message
    # Initializing Dashboard
    dashboard = DashboardPage(driver, base_url)
    dashboard.load()
    # After Registering, The Driver Should be redirected to Dashboard
    assert dashboard.get_title() == "Dashboard"
    assert dashboard.get_welcome_message() == f"Hello {username}!"
    # Logging Out
    dashboard.logout()
    # Driver Redirected to Login
    assert dashboard.get_title() == "Login"
