import requests

# API Test Script
# Tests the retrieval of a webpage
def test_get_webpage():
    response = requests.get("http://localhost:8080/")
    if response.status_code == 200:
        return {"ok": True, "message": "Webpage retrieved successfully"}
    else:
        return {"ok": False, "error": response.json().get("error", "Unknown error")}

# Tests user registration
def test_register_user(name, password):
    url = "http://localhost:8080/register"
    payload = {
        "username": name,
        "password": password,
        "password_confirmation": password
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return {"ok": True, "message": "Registration successful"}
    else:
        return {"ok": False, "error": response.json().get("error", "Unknown error")}
# Test login
def test_login_user(name, password):
    url = "http://localhost:8080/login"
    payload = {
        "username": name,
        "password": password
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return {"ok": True, "message": "Login successful", "session": response.cookies['session']}
    else:
        return {"ok": False, "error": response.json().get("error", "Unknown error")}

#Test Domain retrieval (non expected)
def test_get_domains(session_cookie):
    url = "http://localhost:8080/dashboard"
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"session={session_cookie}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return {"ok": True, "message": "Dashboard retrieved successfully"}
    else:
        return {"ok": False, "error": response.json().get("error", "Unknown error")}

# Test User credentials
testUser = "testuser"
testPass = "Testpass123"

#Test the webpage retrieval
print (f"Get webpage: {test_get_webpage()}")

#Test user registration
register_result = test_register_user(testUser, testPass)
print (f"Register user result: {register_result}")

#Test user login
login_result = test_login_user(testUser, testPass)
session = login_result["session"]       #Save Session for further tests
print (f"Login user result: {login_result}")

#Test domain retrieval
print (f"{test_get_domains(session)}")