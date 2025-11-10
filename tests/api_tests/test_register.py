import Aux_Library as aux
import pytest
import requests
from UserManagementModule import UserNanager as UM

pytestmark = pytest.mark.prder(1)

ADDRESS = "127.0.0.1"
PORT = "8080"
ENDPOINT = "register"


def request_get(endpoint):
   response = requests.get(f"http://{ADDRESS}:{PORT}/{endpoint}", timeout=1)
   return response  


def request_post_data(endpoint, data):
   response = requests.post(f"http://{ADDRESS}:{PORT}/{endpoint}",data=data, timeout=1)
   return response

def request_post_json(endpoint, json_data):
    response = requests.post(f"http://{ADDRESS}:{PORT}", 
        json=json_data, 
        timeout=1)
    return response
@pytest.mark.order(1)
def test_register_page_access():
    # access to register page is valid
    assert request_get(ENDPOINT).ok == True

@pytest.mark.order(2)
def test_register_invalid_username():
    
    # username empty or backspace 
    expected_response = {"error": "Username invalid."} 
    # Test 1
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": "", "password": "Qwe12345", 
                "password_confirmation": "Qwe12345"})
    assert response.json() == expected response
    # Test 2
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": "", "password": "Qwe12345", 
                "password_confirmation": "Qwe12346"})
    assert response.json() == expected response
    # Test 3
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": "", "password": "Qwe1234", 
                "password_confirmation": "Qwe1234"})
    assert response.json() == expected response
    # Test 4
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": "", "password": "Qwe1234567890", 
                "password_confirmation": "Qwe1234567890"})
    assert response.json() == expected response
    # Test 5 
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": "", "password": "qwe12345", 
                "password_confirmation": "qwe12345"})
    assert response.json() == expected response 
    # Test 6
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": "", "password": "QWE12345", 
                "password_confirmation": "QWE12345"})
    assert response.json() == expected response
    # Test 7
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": "", "password": "Qwertyuiop", 
                "password_confirmation": "Qwertyuiop"})
    assert response.json() == expected response
    # Test 8
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": "", "password": "Qwe12345!", 
                "password_confirmation": "Qwe12345!"})
    assert response.json() == expected response
    # Test 9 
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": " ", "password": "Qwe12345", 
                "password_confirmation": "Qwe12345"})
    assert response.json() == expected response
    
    # username already exists
    existing_username = "test1"
    expected_response = {"error": "Username already taken."}
    # Test 1
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{existing_username}", "password": "Qwe12345", 
                "password_confirmation": "Qwe12345"})
    assert response.json() == expected response
    # Test 2
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{existing_username}", "password": "Qwe12345", 
                "password_confirmation": "Qwe12346"})
    assert response.json() == expected response
    # Test 3
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{existing_username}", "password": "Qwe1234", 
                "password_confirmation": "Qwe1234"})
    assert response.json() == expected response
    # Test 4
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{existing_username}", "password": "Qwe1234567890", 
                "password_confirmation": "Qwe1234567890"})
    assert response.json() == expected response
    # Test 5 
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{existing_username}", "password": "qwe12345", 
                "password_confirmation": "qwe12345"}) 
    assert response.json() == expected response 
    # Test 6
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{existing_username}", "password": "QWE12345", 
                "password_confirmation": "QWE12345"})
    assert response.json() == expected response
    # Test 7
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{existing_username}", "password": "Qwertyuiop", 
                "password_confirmation": "Qwertyuiop"})
    assert response.json() == expected response
    # Test 8
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{existing_username}", "password": "Qwe12345!", 
                "password_confirmation": "Qwe12345!"})
    assert response.json() == expected response

@pytest.mark.order(3)
def test_register_invalid_password_confirmation():
    # checking if password and password confirmation are the same
    expected_response = {"error": "Password and Password Confirmation are not the same."}
    username = "test57"
    # Test 1
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe12345", 
                "password_confirmation": "Qwe12346"})
    assert response.json() == expected response
    # Test 2
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe12345", 
                "password_confirmation": "Qwe1234"})
    assert response.json() == expected response
    # Test 3
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe123456", 
                "password_confirmation": "Qwe12345"})
    assert response.json() == expected response
    # Test 4
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe1234567891", 
                "password_confirmation": "Qwe12345678901"})
    assert response.json() == expected response
    # Test 5 
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "qwe12345", 
                "password_confirmation": "Qwe12345"}) 
    assert response.json() == expected response 
    # Test 6
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "QWE12345", 
                "password_confirmation": "Qwe12345"})
    assert response.json() == expected response
    # Test 7
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwertyuiop", 
                "password_confirmation": "Qwertyuiopq"})
    assert response.json() == expected response
    # Test 8
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe12345!", 
                "password_confirmation": "Qwe12345"})
    assert response.json() == expected response

@pytest.mark.order(4)
def test_register_invalid_password():
    # password not long enough - less than 8 characters
    expected_response = {"error": "Password is not between 8 to 12 characters."}
    username = "test57"
    # Test 1
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe1234", 
                "password_confirmation": "Qwe1234"})
    assert response.json() == expected response
    # Test 2
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe123", 
                "password_confirmation": "Qwe123"})
    assert response.json() == expected response
    # Test 3
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "qwe1234", 
                "password_confirmation": "qwe1234"})
    assert response.json() == expected response
    # Test 4
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "QWE123", 
                "password_confirmation": "QWE123"})
    assert response.json() == expected response
    # Test 5 
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwert", 
                "password_confirmation": "Qwert"})
    assert response.json() == expected response
    # Test 8
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe12!", 
                "password_confirmation": "Qwe12!})
    assert response.json() == expected response
    
    # password too long - more than 12 characters
    expected_response = {"error": "Password is not between 8 to 12 characters."}
    # Test 1
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe1234567890", 
                "password_confirmation": "Qwe1234567890"})
    assert response.json() == expected response
    # Test 2
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe123456789012", 
                "password_confirmation": "Qwe123456789012"})
    assert response.json() == expected response
    # Test 3
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "qwe1234567890", 
                "password_confirmation": "qwe1234567890"})
    assert response.json() == expected response
    # Test 4
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "QWE1234567890", 
                "password_confirmation": "QWE1234567890"})
    assert response.json() == expected response
    # Test 5 
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwertyuiopasd", 
                "password_confirmation": "Qwertyuiopasd"})
    assert response.json() == expected response
    # Test 8
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe123456789!", 
                "password_confirmation": "Qwe123456789!})
    assert response.json() == expected response
    
    # password not include at least one uppercase character
    expected_response = {"error": "Password does not include at least one uppercase character."}
    # Test 1 
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "qwe12345", 
                "password_confirmation": "qwe12345"}) 
    assert response.json() == expected response 
    # Test 2
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "qwertyuiop", 
                "password_confirmation": "qwertyuiop"})
    assert response.json() == expected response
    # Test 3
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "qwe12345!", 
                "password_confirmation": "qwe12345!"})
    assert response.json() == expected response
    
    # password not include at least one lowercase character
    expected_response = {"error": "Password does not include at least one lowercase character."}
    # Test 1 
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "QWE12345", 
                "password_confirmation": "QWE12345"}) 
    assert response.json() == expected response 
    # Test 2
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "QWERTYUIOP", 
                "password_confirmation": "QWERTYUIOP"})
    assert response.json() == expected response
    # Test 3
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "QWE12345!", 
                "password_confirmation": "QWE12345!"})
    assert response.json() == expected response
    
    # password not include at least one digits
    expected_response = {"error": "Password does not include at least one digit."}
    # Test 1
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwertyuiop", 
                "password_confirmation": "Qwertyuiop"})
    assert response.json() == expected response
    # Test 2
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwertyuiop!", 
                "password_confirmation": "Qwertyuiop!"})
    assert response.json() == expected response

    # password include characters that are not uppercase, lowercase or digits
    expected_response = {"error": "Password does not include at least one digit."}
    # Test 1
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe12345!", 
                "password_confirmation": "Qwe12345!"})
    assert response.json() == expected response



@pytest.mark.order(-1)
def test_register_successful_registration():
    # check the registration of fully valid users 
    username = "test57"
    expected_response = {"message" : "Registered Successfully"}
    # Test 1
    response = request_post_json(endpoint=ENDPOINT, 
                json_data={"username": f"{username}", 
                "password": "Qwe12345", 
                "password_confirmation": "Qwe12345"})
    assert response.json() == expected response
    
    # Removing new test user
    UM().remove_user(username)



