import pytest
import os
import time
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from tests.selenium_tests.pages.login_page import LoginPage
from tests.selenium_tests.pages.single_domain_modal import SingleDomainModal

pytestmark = pytest.mark.order(10)
THIS_DIR = os.path.dirname(__file__)

@pytest.mark.order(21)
@pytest.mark.parametrize(
    "domain,status,ssl_issuer,ssl_expiration", 
    [
        ("facebook.com", "Live", "DigiCert Inc", "2025-11-26"),
        ("google.com", "Live", "Google Trust Services", "2026-01-19"),
        ("google.fyi", "Down", "N/A", "N/A"),
        ("httpforever.com", "Live", "N/A", "N/A"),
    ]
)
def test_bulk_upload_ui(driver, base_url, domain, status, ssl_issuer, ssl_expiration):
    login_page = LoginPage(driver, base_url)
    login_page.load()
    login_page.login("Selenium_Tester_12345", "St87654321")
    time.sleep(1)
    # Wait until dashboard loads
    single_modal = SingleDomainModal(driver=driver, base_url=base_url)
    single_modal.load()
    time.sleep(1)
    #dashboard.wait_for(locator=dashboard.welcome_message)
    assert single_modal.get_title() == "Dashboard"
    # _modal inherit from DashboardPage
    assert "Selenium_Tester_12345" in single_modal.get_welcome_message()
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
    single_modal.open_add_domain_modal()
    time.sleep(0.5)
    # Step 2: CHEC domain file

    # Step 3: add single domain to dashboard
    single_modal.add_single_domain(domain=domain)
    assert single_modal.wait_for_success()
    
    # Step 4: wait until dashboard is active again
    single_modal.wait_for_active_dashboard()

    # Step 6: Verify results
    domain_details_dashboard = single_modal.get_domain_data(domain=domain)
    # Validate domain exists
    assert domain_details_dashboard is not None
    # Validate status
    assert domain_details_dashboard["status"] == status
    # Validate SSL issuer
    assert domain_details_dashboard["ssl_issuer"].lower() == ssl_issuer.lower()
    # Validate Expiration - only not empty
    assert domain_details_dashboard["ssl_expiration"] and domain_details_dashboard["ssl_expiration"] != "None" 

    # print("[OK] Bulk upload UI test passed.")
