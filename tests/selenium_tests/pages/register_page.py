from selenium.webdriver.common.by import By
from base_page import BasePage

class RegisterPage(BasePage):
    # Locators:
    username_input = (By.ID, "username")
    password_input = (By.ID, "password")
    password_confirmation_input = (By.ID, "password_confirmation")
    register_button = (By.CSS_SELECTOR, "input[type='submit'][value='Register']")
    login_click_here_text = (By.LINK_TEXT, "Click Here")
    # Actions:
    def enter_username(self, username):
        self.type(self.username_input, username)

    def enter_password(self, password):
        self.type(self.password_input, password)

    def enter_password_confirmation(self, password_confirmation):
        self.type(self.password_confirmation_input, password_confirmation)

    def click_register(self):
        self.click(self.register_button)

    def register(self, username, password, password_confirmation):
        self.enter_username(username)
        self.enter_password(password)
        self.enter_password_confirmation(password_confirmation)
        self.register_button.click()
    
    def move_to_login_page(self):
        self.click(self.login_click_here_text)