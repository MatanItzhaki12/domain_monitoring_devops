import requests

# API Test Script
# Tests the retrieval of a webpage
def test_get_webpage(path="/"):
    response = requests.get(f"http://localhost:8080{path}")
    if response.status_code == 200:
        return {"ok": True, "message": "Webpage retrieved successfully"}
    else:
        return {"ok": False, "error": response.json().get("error", "Unknown error")}

# Tests user registration
def test_register_user(name, password, password_confirmation):
    url = "http://localhost:8080/register"
    payload = {
        "username": name,
        "password": password,
        "password_confirmation": password_confirmation
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return {"ok": True, "message": response.json().get("message", "Registration successful")}
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
def check_dashboard(session_cookie):
    url = "http://localhost:8080/dashboard"
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"session={session_cookie}"
    }

    response = requests.get(url, headers=headers)
    return response.text