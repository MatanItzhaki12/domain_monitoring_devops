import time
from selenium.webdriver.common.by import By
from tests.selenium_tests.pages.base_page import BasePage
#from pages.single_domain_modal import SingleDomainModal

class DashboardPage(BasePage):
    PATH = f"/dashboard"
    # Locators:
    welcome_message = (By.ID, "greeting")
    add_domain_button = (By.ID, "openAddDomain")
    logout_button = (By.ID, "logoutBtn")
    scan_now_button = (By.ID, "scanNowBtn")
    # Actions:   
    def get_welcome_message(self):
        return self.get_text(locator=self.welcome_message)

    # def open_add_single_domain(self):
    #     self.click(self.add_domain_button)
    #     from tests.selenium_tests.pages.single_domain_modal import SingleDomainModal
    #     return SingleDomainModal(self.driver)

    def logout(self):
        time.sleep(0.5)
        self.click(locator=self.logout_button)
        time.sleep(1)

    def scan_now(self):
        self.click(locator=self.scan_now_button)

    def open_add_single_domain(self):
        self.click(self.add_domain_button)
        from tests.selenium_tests.pages.single_domain import SingleDomainModal
        modal = SingleDomainModal(self.driver, self.base_url)
        modal.wait_until_open()
        return modal