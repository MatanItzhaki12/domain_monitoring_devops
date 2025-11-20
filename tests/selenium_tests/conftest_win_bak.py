import pytest
import os
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Global Fixtures

@pytest.fixture()
def driver():

    options = Options()
    options.add_argument("--headless=new")  # optional

    os_name = platform.system()

    # --- Linux-specific fixes ---
    if os_name == "Linux":
        # If using Chromium instead of Chrome
        # Try both common binary locations
        for path in ["/usr/bin/chromium-browser", "/usr/bin/chromedriver", "/usr/bin/chromium"]:
            try:
                with open(path):
                    options.binary_location = path
                    break
            except:
                pass
        # (If Chrome is installed, binary_location isn't needed)

        # Required flags on Linux / CI / Docker
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.implicitly_wait(5)
    yield driver
    driver.quit()

@pytest.fixture
def base_url():
    return os.getenv("BASE_URL", "http://localhost:8080")
