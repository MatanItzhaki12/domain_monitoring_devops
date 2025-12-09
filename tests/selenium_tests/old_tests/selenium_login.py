from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def login(driver):
    # Wait for login button
    btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".btn.login"))
    )
    if btn is None:
        raise Exception("Login button not found")

    btn.click()

    # Wait for login form
    form = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "login-form"))
    )
    if form is None:
        raise Exception("Login form did not appear")

    # Fields
    username = driver.find_element(By.ID, "username")
    password = driver.find_element(By.ID, "password")

    if username is None:
        raise Exception("Username field missing")
    if password is None:
        raise Exception("Password field missing")

    # Fill form
    username.send_keys("john_doe")
    password.send_keys("password" + Keys.RETURN)

    # Validate login (change selector to your success UI)
    dashboard = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "dashboard-content"))
    )
    if dashboard is None:
        raise Exception("Dashboard did not load after login")
    print("Login successful.")
