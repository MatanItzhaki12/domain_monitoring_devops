from selenium.webdriver.common.by import By
from tests.selenium_tests.pages.base_page import BasePage



class LoginPage(BasePage):
    PATH = f"/login"
    # Locators:
    username_input = (By.ID, "username")
    password_input = (By.ID, "password")
    login_button = (By.CSS_SELECTOR, "input[type='submit'][value='Login']")
    register_button = (By.ID, "register")
    error_locator = (By.ID, "failed-login")
    # Actions:
    def enter_username(self, username):
        self.type(self.username_input, username)

    def enter_password(self, password):
        self.type(self.password_input, password)

    def click_login(self):
        self.click(self.login_button)

    def login(self, username, password):
        self.load()
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    def move_to_login_page(self):
        self.click(self.register_button)
