
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium_tests.pages.base_page import BasePage


class SingleDomainModal(BasePage):

    modal = (By.ID, "addDomainModal")
    form = (By.ID, "addDomainForm")
    domain_input = (By.ID, "domainInput")
    status_box = (By.ID, "addDomainStatus")
    submit_button = (By.CSS_SELECTOR, "#addDomainForm button[type='submit']")

    def wait_until_open(self):
        self.wait_for(self.modal)
        return self

    def enter_domain(self, domain):
        input_el = self.wait_for(self.domain_input)
        input_el.clear()
        input_el.send_keys(domain)

    def submit(self):
        self.click(self.submit_button)

    def wait_for_success(self):
        
        WebDriverWait(self.driver, 10).until(
            EC.text_to_be_present_in_element(self.status_box, "Domain added")
        )
        return True
