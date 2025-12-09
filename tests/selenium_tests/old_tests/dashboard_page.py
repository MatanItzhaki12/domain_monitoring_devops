from selenium.webdriver.common.by import By
from tests.selenium_tests.pages.base_page import BasePage
from tests.selenium_tests.pages.bulk_upload_modal import BulkUploadModal
#from pages.single_domain_modal import SingleDomainModal
from tests.api_tests.Aux_Library import BASE_URL

class DashboardPage(BasePage):
    URL = f"{BASE_URL}/dashboard"
    # Locators:
    welcome_message = (By.ID, "greeting")
    add_domain_button = (By.ID, "openAddDomain")
    bulk_upload_button = (By.ID, "openBulkUpload")
    bulk_modal_form = (By.ID, "bulkUploadForm")
    logout_button = (By.ID, "logoutBtn")
    scan_now_button = (By.ID, "scanNowBtn")
    # Actions:   
    def get_welcome_message(self):
        return self.get_text(locator=self.welcome_message)

    def open_bulk_upload(self):
        self.click(locator=self.bulk_upload_button)
        self.wait_for(self.bulk_modal_form)
        return BulkUploadModal(self.driver)

    # def open_add_single_domain(self):
    #     self.click(self.add_domain_button)
    #     from tests.selenium_tests.pages.single_domain_modal import SingleDomainModal
    #     return SingleDomainModal(self.driver)

    def logout(self):
        self.click(locator=self.logout_button)

    def scan_now(self):
        self.click(locator=self.scan_now_button)


from selenium.webdriver.common.by import By
from tests.selenium_tests.pages.base_page import BasePage
from tests.selenium_tests.pages.bulk_upload_modal import BulkUploadModal
#from tests.selenium_tests.pages.single_domain_modal import SingleDomainModal
from tests.api_tests.Aux_Library import BASE_URL



class DashboardPage(BasePage):
    URL = f"{BASE_URL}/dashboard"
    # Locators:
    welcome_message = (By.ID, "greeting")
    add_domain_button = (By.ID, "openAddDomain")
    bulk_upload_button = (By.ID, "openBulkUpload")
    logout_button = (By.ID, "logoutBtn")
    scan_now_button = (By.ID, "scanNowBtn")
    # Actions:   
    def get_welcome_message(self):
        return self.get_text(locator=self.welcome_message)

    def open_bulk_upload(self):
        self.click(self.bulk_upload_button)
        return BulkUploadModal(self.driver)

    # def open_add_single_domain(self):
    #     self.click(self.add_domain_button)
    #     return SingleDomainModal(self.driver)

    def logout(self):
        self.click(locator=self.logout_button)

    def scan_now(self):
        self.click(locator=self.scan_now_button)

