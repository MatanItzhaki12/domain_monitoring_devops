from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pytest

from tests.selenium_tests.pages.login_page import LoginPage
from tests.selenium_tests.pages.dashboard_page import DashboardPage

BASE_URL = "http://localhost:8080"

SEL_TEST_USERNAME = "selsingletest"
SEL_TEST_PASSWORD = "123456Aae"

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

def login_and_get_dash(driver):
    """
    Logging in through the UI so we can reach the Dashboard
    ready to use and bring back DashboardPage object
    """
    login_page = LoginPage(driver, BASE_URL)
    login_page.login(SEL_TEST_USERNAME, SEL_TEST_PASSWORD)

    dashboard_page = DashboardPage(driver, BASE_URL)
    dashboard_page.wait_for(dashboard_page.add_domain_button)

    return dashboard_page
    

def add_single_domain_and_result(driver):
    """
    Check the Add Single Domain UI + Results
    """

    ###dashboard_page = login_and_get_dashboard(driver)
    
    #login trhough UI and reaching Dashboard
    
    ###modal = dashboard_page.open_add_single_domain()
    
    test_domain = "https://google.com"
    plain_domain = "google.com"

    ###modal.enter_domain(test_domain)
    ###modal.submit()
    


    #single_domain_input = wait.until(
        #EC.visibility_of_element_located((By.ID, "singleDomainInput"))
                                    #)
    #single_domain_input.clear()
    







