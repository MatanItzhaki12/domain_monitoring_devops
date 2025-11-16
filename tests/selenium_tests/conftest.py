import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def browser():
    # For headless mode:
    # options = Options()
    # options.add_argument("--headless=new")
    
    # Installing Browser:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    # For headless mode:
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Optional:
    driver.maximize_window()
    driver.implicitly_wait(5)
    # Yield\Return the driver to the test
    yield driver 
    # Quit when done
    driver.quit()   


