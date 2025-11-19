import pytest
from tests.selenium_tests.pages.dashboard_page import DashboardPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from tests.selenium_tests.pages.login_page import LoginPage


pytestmark = pytest.mark.order(8)

# --------
# Negative tests: invalid login
# --------
@pytest.mark.parametrize(
    "username,password",
    [
        ("john_doe", "wrong_password"),
        ("wrong_user", "password"),
        ("", "password"),
        ("john_doe", ""),
        ("", ""),
    ],
)
def test_1_login_invalid(driver, base_url, username, password):
    login_page = LoginPage(driver, base_url)

    login_page.load()
    login_page.login(username, password)

    # Check for error message visibility and content
    assert login_page.get_text(login_page.error_locator) == "Invalid username or password"
    assert login_page.is_visible(login_page.error_locator) == True

    # Extra safety: user should *not* be on dashboard
    assert "dashboard" not in driver.title.lower()


# --------
# Positive test: valid login
# --------
def test_2_login_valid(driver, base_url):
    login_page = LoginPage(driver, base_url)
    dashboard_page = DashboardPage(driver, base_url)
    # Go to login page
    login_page.load()

    # Perform login
    login_page.login("john_doe", "password")
    # Assert by title
    WebDriverWait(driver, 5).until(
        lambda d: "Dashboard" in d.title
    )
    assert "Dashboard" in login_page.get_title()
