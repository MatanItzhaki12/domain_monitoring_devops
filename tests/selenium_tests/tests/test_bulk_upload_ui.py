import pytest
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from tests.selenium_tests.pages.login_page import LoginPage
from tests.selenium_tests.pages.dashboard_page import DashboardPage
from tests.selenium_tests.utils.domain_factory import generate_domain_file

pytestmark = pytest.mark.order(10)
THIS_DIR = os.path.dirname(__file__)


def test_bulk_upload_ui(driver, base_url):
    login_page = LoginPage(driver, base_url)
    login_page.load()
    login_page.login("Selenium_Tester_12345", "St87654321")

    # Wait until dashboard loads
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "greeting"))
    )

    dashboard = DashboardPage(driver, base_url)

    # =========================
    #  BULK UPLOAD TEST
    # =========================

    # Step 1: open modal
    modal = dashboard.open_bulk_upload()

    # Step 2: create domain file
    file_path, domains = generate_domain_file(THIS_DIR)

    # Step 3: upload file
    dashboard = modal.upload_file(file_path)

    # Step 4: wait until dashboard is active again
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "openAddDomain"))
    )

    # Step 5: ensure domains appear in page source
    WebDriverWait(driver, 10).until(
        lambda d: all(domain in d.page_source.lower() for domain in domains)
    )

    print("[OK] Bulk upload UI test passed.")

    # CLEANUP
    if os.path.exists(file_path):
        os.remove(file_path)
