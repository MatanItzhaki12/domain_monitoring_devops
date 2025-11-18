import pytest
import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from tests.selenium_tests.pages.login_page import LoginPage
from tests.selenium_tests.pages.dashboard_page import DashboardPage
from tests.selenium_tests.pages.bulk_upload_modal import BulkUploadModal
from tests.selenium_tests.utils.domain_factory import generate_domain_file

pytestmark = pytest.mark.order(10)
THIS_DIR = os.path.dirname(__file__)

@pytest.mark.order(21)
def test_bulk_upload_ui(driver, base_url):
    login_page = LoginPage(driver, base_url)
    login_page.load()
    login_page.login("Selenium_Tester_12345", "St87654321")
    time.sleep(1)
    # Wait until dashboard loads
    dashboard = DashboardPage(driver, base_url)
    dashboard.load()
    time.sleep(1)
    #dashboard.wait_for(locator=dashboard.welcome_message)
    assert dashboard.get_title() == "Dashboard"
    assert "Selenium_Tester_12345" in dashboard.get_welcome_message()
    time.sleep(1)
    # WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.ID, "greeting"))
    # )

    # dashboard = DashboardPage(driver, base_url)

    # =========================
    #  BULK UPLOAD TEST
    # =========================

    # Step 1: open modal

    # dashboard.open_bulk_upload()
    bulk_modal = BulkUploadModal(driver=driver, base_url=base_url)
    bulk_modal.open_bulk_upload()
    time.sleep(0.5)
    # Step 2: create domain file
    file_path, domains = generate_domain_file(THIS_DIR)

    # Step 3: upload file
    bulk_modal.upload_bulk(file_path=file_path)
    assert bulk_modal.get_final_status() == "Bulk upload completed!"
    
    # Step 4: wait until dashboard is active again
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "openAddDomain"))
    )

    # Step 5: ensure domains appear in page source
    assert WebDriverWait(driver, 10).until(
        lambda d: all(domain in d.page_source.lower() for domain in domains)
    ), "Not all domains are present on the page"

    # print("[OK] Bulk upload UI test passed.")

    # CLEANUP
    if os.path.exists(file_path):
        os.remove(file_path)
