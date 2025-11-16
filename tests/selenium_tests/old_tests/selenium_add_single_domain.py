from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import pytest

BASE_URL = "http://localhost:8080"

@pytest.fixture
def driver():
    """
    Creating a Chrome WebDriver instance
    """
    options = options()

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)

    yield driver
    driver.quit()

def login(driver, username: str, password: str):
    """
    Logging in through the UI so we can reach the Dashboard
    """
    driver.get(f"{BASE_URL}/login")

    user_input = driver.find_element(By.ID, "username")
    pass_input = driver.find_element(By.ID, "password")
    login_submit = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")

    user_input.clear()
    user_input.send_keys(username)

    pass_input.clear()
    pass_input.send_keys(password)

    login_submit.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "openAddDomain"))
                                    )

def add_single_domain_and_result(driver):
    pass






