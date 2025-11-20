import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


class BasePage:
    PATH = "/"

    def __init__(self, driver, base_url):
        self.driver = driver
        self.wait = WebDriverWait(driver=self.driver, timeout=10)
        self.base_url = base_url
    # Actions:
    def load(self):
        self.driver.get(f"{self.base_url}{self.PATH}")
    
    def get_title(self):
        return self.driver.title

    def click(self, locator):
        element = self.wait.until(EC.element_to_be_clickable(locator))
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click().perform()

    def wait_for(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator=locator))

    def wait_for_multiple_elements(self, locator):
        return self.wait.until(EC.visibility_of_all_elements_located(locator=locator))
    
    def wait_for_element_to_close(self, locator):
        return self.wait.until(EC.invisibility_of_element_located(locator=locator))

    def wait_for_specific_message(self, locator, message):
        return self.wait.until(EC.text_to_be_present_in_element(
            locator, message))
    
    def type(self, locator, text):
        self.wait_for(locator=locator).send_keys(text)
    
    def get_text(self, locator):
        return self.wait_for(locator=locator).text

    def is_visible(self, locator):
        try:
            self.wait_for(locator=locator)
            return True
        except Exception as e:
            return False
        
    def upload_file_enter_path(self, locator, file_path):
        # 1. Convert to absolute path
        abs_file_path =os.path.abspath(file_path)
        # 2. Verify file exists locally before trying to upload
        if not os.path.exists(abs_file_path):
            raise FileNotFoundError(f"File not found: {abs_file_path}")
        # 3. Use presence_of_element_located instead of visibility (input is hidden)
        element = self.wait.until(EC.presence_of_element_located(locator))
        # 4. Send the keys
        element.send_keys(abs_file_path)