import pytest
import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException, TimeoutException, NoAlertPresentException
import json
from tests.selenium_tests.pages.login_page import LoginPage
from tests.selenium_tests.pages.single_domain_modal import SingleDomainModal

pytestmark = pytest.mark.order(9)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
USERS_DATA_DIR = os.path.join(PROJECT_ROOT, "UsersData")

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
    wait = WebDriverWait(driver, 25)

    # 1. LOGIN
    login_page = LoginPage(driver, base_url)
    login_page.load()
    login_page.login("Selenium_Tester_12345", "St87654321")
    wait.until(EC.url_contains("/dashboard"))

    # 2. LOAD DASHBOARD (Robust)
    single_modal = SingleDomainModal(driver=driver, base_url=base_url)
    single_modal.load()
    
    # FIX: Handle "Scan failed" alert appearing immediately on load
    try:
        wait.until(lambda d: single_modal.get_title() == "Dashboard")
    except UnexpectedAlertPresentException:
        print("[WARN] Alert detected during Dashboard load. dismissing...")
        try:
            driver.switch_to.alert.accept()
        except NoAlertPresentException:
            pass
        # Retry waiting for title
        wait.until(lambda d: single_modal.get_title() == "Dashboard")

    wait.until(lambda d: "Selenium_Tester_12345" in single_modal.get_welcome_message())

    # =========================
    #  Add Single Domain w/ RETRY
    # =========================
    max_retries = 5
    success = False

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries}: Adding domain {domain}")
            single_modal.open_add_domain_modal()
            single_modal.add_single_domain(domain=domain)
            
            if single_modal.wait_for_success():
                single_modal.wait_for_active_dashboard()
                success = True
                break 
        
        except UnexpectedAlertPresentException:
            print(f"[WARN] Alert detected on attempt {attempt + 1}. Handling retry...")
            try:
                driver.switch_to.alert.accept()
            except NoAlertPresentException:
                pass
            driver.refresh()
            wait.until(lambda d: single_modal.get_title() == "Dashboard")
            continue
            
        except TimeoutException:
            print(f"[WARN] Timeout on attempt {attempt + 1}. Reloading...")
            driver.refresh()
            wait.until(lambda d: single_modal.get_title() == "Dashboard")
            continue

    if not success:
        pytest.fail(f"Failed to add domain {domain} after {max_retries} attempts.")

    # Step 4: Verify results
    def domain_data_is_ready(d):
        try:
            data = single_modal.get_domain_data(domain=domain)
            if data and data["status"] == status:
                return data
            return False
        except Exception:
            return False

    domain_details_dashboard = wait.until(domain_data_is_ready)

    assert domain_details_dashboard is not None
    assert domain_details_dashboard["status"] == status
    assert domain_details_dashboard["ssl_issuer"].lower() == ssl_issuer.lower()
    assert domain_details_dashboard["ssl_expiration"] and domain_details_dashboard["ssl_expiration"] != "None"

    # CLEANUP
    user_domains_path = os.path.join(USERS_DATA_DIR, "Selenium_Tester_12345_domains.json")
    if os.path.exists(user_domains_path):
        try:
            with open(user_domains_path, "w") as f:
                json.dump([], f)
        except Exception as e:
            print(f"[WARN] Failed to clean up domains file: {e}")