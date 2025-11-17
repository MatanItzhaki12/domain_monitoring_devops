import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.selenium_tests.pages.base_page import BasePage


class BulkUploadModal(BasePage):
    file_input = (By.CSS_SELECTOR, "#bulkUploadForm input[type='file']")
    form = (By.ID, "bulkUploadForm")

    def upload_file(self, file_path):
        wait = WebDriverWait(self.driver, 10)

        # Wait for file input to be present
        file_input_el = wait.until(EC.presence_of_element_located(self.file_input))
        file_input_el.send_keys(file_path)

        # Verify file selection worked
        assert file_input_el.get_attribute("value"), "File selection failed."

        # Wait for form and submit via JavaScript
        form_el = wait.until(EC.presence_of_element_located(self.form))
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('submit', { bubbles: true }));",
            form_el
        )


