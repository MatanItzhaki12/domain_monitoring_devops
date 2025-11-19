
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium_tests.pages.dashboard_page import DashboardPage


class SingleDomainModal(DashboardPage):
    # Locators:
    add_domain_button = (By.ID, "openAddDomain")
    modal = (By.ID, "addDomainModal")
    form = (By.ID, "addDomainForm")
    domain_input = (By.ID, "domainInput")
    status_box = (By.ID, "addDomainStatus")
    submit_button = (By.CSS_SELECTOR, "#addDomainForm button[type='submit']")
    # Actions:
    def wait_for_modal(self):
        self.wait_for(self.modal)

    def open_add_domain_modal(self):
        self.click(locator=self.add_domain_button)
        self.wait_for_modal()

    def enter_domain(self, domain):
        input_el = self.wait_for(self.domain_input)
        input_el.clear()
        input_el.send_keys(domain)

    def submit(self):
        self.click(self.submit_button)

    def add_single_domain(self, domain):
        self.enter_domain(domain=domain)
        self.submit()

    def wait_for_success(self):
        return self.wait_for_specific_message(
            locator=self.status_box,
            message="Domain added successfully" 
            )
    
    def wait_for_modal_to_close(self):
        return self.wait_for_element_to_close(locator=self.modal)
