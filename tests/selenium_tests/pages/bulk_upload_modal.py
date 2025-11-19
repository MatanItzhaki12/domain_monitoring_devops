import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.selenium_tests.pages.dashboard_page import DashboardPage


class BulkUploadModal(DashboardPage):
    # Locators:
    bulk_upload_button = (By.ID, "openBulkUpload")
    file_input = (By.CSS_SELECTOR, "#bulkUploadForm input[type='file']")
    upload_button = (By.CSS_SELECTOR, "#bulkUploadForm button[type='submit']")
    form = (By.ID, "bulkUploadForm")
    upload_status = (By.ID, "bulkUploadStatus")
    bulk_modal = (By.ID, "bulkUploadModal")
    # Actions:
    def open_bulk_upload(self):
        self.click(locator=self.bulk_upload_button)
        self.wait_for(self.bulk_modal)

    def file_upload_enter_path(self, file_path):
        input_file = self.wait.until(EC.presence_of_element_located(self.file_input))
        # modal hide the file input, so we need visible
        self.driver.execute_script("arguments[0].style.display = 'block';", input_file)
        
        self.type(self.file_input, file_path)

    def submit_file(self):
        self.click(locator=self.upload_button)

    def upload_bulk(self, file_path):
        self.file_upload_enter_path(file_path=file_path)
        self.submit_file()

    def _get_upload_message(self):
        element = self.wait.until(EC.presence_of_element_located(self.upload_status))
        message = element.text.strip()
        css = element.get_attribute("class")
        
        # Ignore loading state
        if "status-loading" in css or message.lower().startswith("uploading"):
            return False
        # Return only non-empty message
        if not message:
            return False
        return message 

    def get_final_status(self):
        return WebDriverWait(self.driver, 10).until(
            lambda driver: self._get_upload_message(),
            "Final message did not appear."
        )



