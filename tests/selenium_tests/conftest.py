import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

@pytest.fixture()
def driver():
    chrome_options = Options()

    chrome_options.add_argument("--disable-features=DownloadBubble")  # new in Chrome 110+
    chrome_options.add_argument("--safebrowsing-disable-download-protection")
    chrome_options.add_argument("--safebrowsing-disable-extension-blacklist")
    chrome_options.add_argument("--disable-component-update")
    chrome_options.add_argument("--disable-site-isolation-trials")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")

    # THIS IS THE KEY LINE FOR FILE UPLOADS ON LINUX:
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # Most important for file upload in Linux containers:
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-file-access-from-files")   # sometimes needed

    # Stable headless mode
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")


    chrome_options.add_argument("--allow-file-access-from-files")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--enable-local-file-accesses")
    chrome_options.add_argument("--disable-site-isolation-trials")


    # Safe additional flags
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")

    chrome_options.add_argument("--disable-features=LockProfileForFileUploads,DownloadBubble,DownloadBubbleV2")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    yield driver
    driver.quit()

@pytest.fixture
def base_url():
    return os.getenv("BASE_URL", "http://localhost:8080")