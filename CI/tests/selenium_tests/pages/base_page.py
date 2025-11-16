from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver=self.driver, timeout=5)
        
    def click(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator)).click()
    
    def wait_for(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator=locator))

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