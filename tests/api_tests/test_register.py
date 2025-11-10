import Aux_Library
import pytest
import app.py
import requests

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

def test_register_page_access():
    # access to register page is valid
    assert request_get(ENDPOINT).ok == True

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


def test_register_invalid_password_confirmation():
    # checking if password and password confirmation are the same
    
    pass

def test_register_invalid_password():
    # password not long enough - less than 8 characters

    # password too long - more than 12 characters

    # password not include at least one uppercase character
    
    # password not include at least one lowercase character
    
    # password not include at least one digits

    # password include characters that are not uppercase, lowercase or digits

    # password is valid - and betwwen 8 to 12 characters
    
    pass


def test_register_successful_registration():
    # check the registration of fully valid users 
    
    pass


