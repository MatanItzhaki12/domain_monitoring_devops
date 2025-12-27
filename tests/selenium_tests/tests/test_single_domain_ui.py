import pytest
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.selenium_tests.pages.login_page import LoginPage
from tests.selenium_tests.pages.single_domain_modal import SingleDomainModal

pytestmark = pytest.mark.order(9)

@pytest.mark.parametrize(
    "domain,status,ssl_issuer,ssl_expiration", 
    [
        ("facebook.com", "Live", "DigiCert Inc", "2025-11-26"),
        ("google.com", "Live", "Google Trust Services", "2026-01-19"),
        ("google.fyi", "Down", "N/A", "N/A"),
        ("httpforever.com", "Live", "N/A", "N/A"),
    ]
)
def test_add_single_domain_ui(driver, base_url, domain, status, ssl_issuer, ssl_expiration):
    # Setup explicit wait (25 seconds)
    wait = WebDriverWait(driver, 25)

    # --- RESTORED LOGIN STEPS ---
    login_page = LoginPage(driver, base_url)
    login_page.load()
    login_page.login("Selenium_Tester_12345", "St87654321")
    
    # Wait for successful login
    wait.until(EC.url_contains("/dashboard"))
    # ----------------------------

    single_modal = SingleDomainModal(driver=driver, base_url=base_url)
    single_modal.load()
    
    wait.until(lambda d: single_modal.get_title() == "Dashboard")
    wait.until(lambda d: "Selenium_Tester_12345" in single_modal.get_welcome_message())

    # =========================
    #  Add Single Domain TEST
    # =========================
    single_modal.open_add_domain_modal()
    
    single_modal.add_single_domain(domain=domain)
    assert single_modal.wait_for_success()
    
    single_modal.wait_for_active_dashboard()

    # Step 4: Verify results
    def domain_data_is_ready(d):
        try:
            data = single_modal.get_domain_data(domain=domain)
            # Return data only if it exists AND status matches expected
            if data and data["status"] == status:
                return data
            return False
        except Exception:
            return False

    # Wait for data to populate
    domain_details_dashboard = wait.until(domain_data_is_ready)

    assert domain_details_dashboard is not None
    assert domain_details_dashboard["status"] == status
    assert domain_details_dashboard["ssl_issuer"].lower() == ssl_issuer.lower()
    assert domain_details_dashboard["ssl_expiration"] and domain_details_dashboard["ssl_expiration"] != "None"