import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

@pytest.fixture()
def driver():
    chrome_options = Options()

    # Stable headless mode
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")

    # Required for Linux stability
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    # IMPORTANT: Required for file uploads, cookies, storage, stability
    chrome_options.add_argument("--user-data-dir=/tmp/chrome-profile")
    chrome_options.add_argument("--profile-directory=Default")

    chrome_options.add_argument("--allow-file-access-from-files")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--enable-local-file-accesses")
    chrome_options.add_argument("--disable-site-isolation-trials")


    # Safe additional flags
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    yield driver
    driver.quit()

@pytest.fixture
def base_url():
    return os.getenv("BASE_URL", "http://localhost:8080")