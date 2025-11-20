import os
import pytest
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

@pytest.fixture()
def driver():
    chrome_options = Options()

    chrome_options.add_argument("--disable-features=DownloadBubble")
    chrome_options.add_argument("--safebrowsing-disable-download-protection")
    chrome_options.add_argument("--safebrowsing-disable-extension-blacklist")
    chrome_options.add_argument("--disable-component-update")
    chrome_options.add_argument("--disable-site-isolation-trials")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")

    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-file-access-from-files")
    chrome_options.add_argument("--enable-local-file-accesses")

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")

    # -------- FIX: auto-detect chromedriver ----------
    driver_path = shutil.which("chromedriver")
    if not driver_path:
        raise RuntimeError("chromedriver not found in PATH")

    service = Service(driver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)

    yield driver
    driver.quit()


@pytest.fixture
def base_url():
    return os.getenv("BASE_URL", "http://localhost:8080")
