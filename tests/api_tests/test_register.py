from .Aux_Library import check_get_webpage, check_register_user, remove_user_from_running_app as remove_user
import pytest
from UserManagementModule import UserManager as UM

pytestmark = pytest.mark.order(2)

# Fixtures

@pytest.fixture(scope="module")
def existing_username():
    return "test1"

@pytest.fixture(scope="module")
def new_username():
    return "test57"

# Tests

def test_1_register_page_access():
    # Check if the /register page is accessible
    assert check_get_webpage("/register").ok == True

# Invalid Username Tests

@pytest.mark.parametrize(
    "username,password,password_confirmation",
    [
        # Empty or space username
        ("", "Qwe12345", "Qwe12345"),
        ("", "Qwe12345", "Qwe12346"),
        ("", "Qwe1234", "Qwe1234"),
        ("", "Qwe1234567890", "Qwe1234567890"),
        ("", "qwe12345", "qwe12345"),
        ("", "QWE12345", "QWE12345"),
        ("", "Qwertyuiop", "Qwertyuiop"),
        ("", "Qwe12345!", "Qwe12345!"),
        (" ", "Qwe12345", "Qwe12345")
    ]
)
def test_2_register_invalid_username(username, password, password_confirmation): 
    # Invalid or empty username should be rejected
    expected_response = {"error": "Username invalid."} 
    response = check_register_user(username=username, password=password, 
                                   password_confirmation=password_confirmation)
    assert response.status_code == 400
    assert response.json() == expected_response
    
@pytest.mark.parametrize(
    "password,password_confirmation",
    [
        ("Qwe12345", "Qwe12345"),
        ("Qwe12345", "Qwe12346"),
        ("Qwe1234", "Qwe1234"),
        ("Qwe1234567890", "Qwe1234567890"),
        ("qwe12345", "qwe12345"),
        ("QWE12345", "QWE12345"),
        ("Qwertyuiop", "Qwertyuiop"),
        ("Qwe12345!", "Qwe12345!")
    ]
)
def test_3_register_existing_username(existing_username, password, password_confirmation):

    # username already exists
    expected_response = {"error": "Username already taken."}
    response = check_register_user(username=existing_username, password=password, 
                                   password_confirmation=password_confirmation)
    assert response.status_code == 409
    assert response.json() == expected_response

# Invalid Password Confirmatiom Tests

@pytest.mark.parametrize(
    "password,password_confirmation",
    [
        ("Qwe12345", "Qwe12346"),
        ("Qwe12345", "Qwe1234"),
        ("Qwe123456", "Qwe12345"),
        ("Qwe1234567891", "Qwe12345678901"),
        ("qwe12345", "Qwe12345"),
        ("QWE12345", "Qwe12345"),
        ("Qwertyuiop", "Qwertyuiopq"),
        ("Qwe12345!", "Qwe12345")
    ]
)
def test_4_register_invalid_password_confirmation(new_username, password, password_confirmation):
    # checking if password and password confirmation are the same
    expected_response = {"error": "Password and Password Confirmation are not the same."}
    response = check_register_user(username=new_username, password=password, 
                                   password_confirmation=password_confirmation)
    assert response.status_code == 400
    assert response.json() == expected_response
    
# Invalid Password Tests   

@pytest.mark.parametrize(
    "password,password_confirmation,expected_response",
    [
        # password not long enough - less than 8 characters
        ("Qwe1234", "Qwe1234", {"error": "Password is not between 8 to 12 characters."}),
        ("Qwe123", "Qwe123", {"error": "Password is not between 8 to 12 characters."}),
        ("qwe1234", "qwe1234", {"error": "Password is not between 8 to 12 characters."}),
        ("QWE123", "QWE123", {"error": "Password is not between 8 to 12 characters."}),
        ("Qwert", "Qwert", {"error": "Password is not between 8 to 12 characters."}),
        ("Qwe12!", "Qwe12!", {"error": "Password is not between 8 to 12 characters."}),    
        # password too long - more than 12 characters
        ("Qwe1234567890", "Qwe1234567890", {"error": "Password is not between 8 to 12 characters."}),
        ("Qwe123456789012", "Qwe123456789012", {"error": "Password is not between 8 to 12 characters."}),
        ("qwe1234567890", "qwe1234567890", {"error": "Password is not between 8 to 12 characters."}),
        ("QWE1234567890", "QWE1234567890", {"error": "Password is not between 8 to 12 characters."}),
        ("Qwertyuiopasd", "Qwertyuiopasd", {"error": "Password is not between 8 to 12 characters."}),
        ("Qwe123456789!", "Qwe123456789!", {"error": "Password is not between 8 to 12 characters."}),
        # password does not include at least one uppercase character
        ("qwe12345", "qwe12345", {"error": "Password does not include at least one uppercase character."}),
        ("qwertyuiop", "qwertyuiop", {"error": "Password does not include at least one uppercase character."}),
        ("qwe12345!", "qwe12345!", {"error": "Password does not include at least one uppercase character."}),
        # password does not include at least one lowercase character
        ("QWE12345", "QWE12345", {"error": "Password does not include at least one lowercase character."}),
        ("QWERTYUIOP", "QWERTYUIOP", {"error": "Password does not include at least one lowercase character."}),
        ("QWE12345!", "QWE12345!", {"error": "Password does not include at least one lowercase character."}),
        # password does not include at least one digits
        ("Qwertyuiop", "Qwertyuiop", {"error": "Password does not include at least one digit."}),
        ("Qwertyuiop!", "Qwertyuiop!", {"error": "Password does not include at least one digit."}),
        # password include characters that are not uppercase, lowercase or digits
        ("Qwe12345!", "Qwe12345!", {"error": "Password should include only uppercase characters, lowercase characters and digits!"})
    ]

)
def test_5_register_invalid_password(new_username, password, password_confirmation, expected_response):
    # Invalid password formats should be rejected
    response = check_register_user(username=new_username, password=password, 
                                   password_confirmation=password_confirmation)
    assert response.status_code == 400
    assert response.json() == expected_response


def test_6_register_successful_registration(new_username):
    # check the registration of fully valid users 
    expected_response = {"message" : "Registered Successfully."}
    # Test 1
    response = check_register_user(username=new_username, password="Qwe12345", 
                                   password_confirmation="Qwe12345")
    assert response.status_code == 201
    assert response.json() == expected_response
    
    # Removing new test user
    # UM().remove_user(new_username)
    # results = get("/reload_users_to_memory")
    remove_user(new_username)

