import pytest
import os
import json
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException, TimeoutException, NoAlertPresentException

from tests.selenium_tests.pages.login_page import LoginPage
from tests.selenium_tests.pages.bulk_upload_modal import BulkUploadModal
from tests.selenium_tests.utils.domain_factory import generate_fixed_domain_file, remove_fixed_file_path

pytestmark = pytest.mark.order(10)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(TEST_DIR, "selenium_temp")
os.makedirs(TEMP_DIR, exist_ok=True)

PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, "..", "..", ".."))
USERS_DATA_DIR = os.path.join(PROJECT_ROOT, "UsersData")

def test_1_bulk_upload_ui(driver, base_url):
    wait = WebDriverWait(driver, 25)

    # 1. LOGIN
    login_page = LoginPage(driver, base_url)
    login_page.load()
    login_page.login("Selenium_Tester_12345", "St87654321")
    wait.until(EC.url_contains("/dashboard"))

    # 2. LOAD DASHBOARD (Robust)
    bulk_modal = BulkUploadModal(driver=driver, base_url=base_url)
    bulk_modal.load()
    
    # FIX: Handle "Scan failed" alert appearing immediately on load
    try:
        wait.until(lambda d: bulk_modal.get_title() == "Dashboard")
    except UnexpectedAlertPresentException:
        print("[WARN] Alert detected during Dashboard load. dismissing...")
        try:
            driver.switch_to.alert.accept()
        except NoAlertPresentException:
            pass
        # Retry waiting for title
        wait.until(lambda d: bulk_modal.get_title() == "Dashboard")
        
    wait.until(lambda d: "Selenium_Tester_12345" in bulk_modal.get_welcome_message())

    # =========================
    #  BULK UPLOAD w/ RETRY
    # =========================
    domains_file_path, check_domains_json_path, domains = generate_fixed_domain_file(TEMP_DIR)
    
    max_retries = 5
    success = False

    try:
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries}: Uploading bulk file...")
                bulk_modal.open_bulk_upload()
                bulk_modal.upload_bulk(file_path=domains_file_path)
                wait.until(lambda d: bulk_modal.get_final_status() == "Bulk upload completed!")
                bulk_modal.wait_for_active_dashboard()
                success = True
                break 

            except UnexpectedAlertPresentException:
                print(f"[WARN] Alert detected on attempt {attempt + 1}. Handling retry...")
                try:
                    driver.switch_to.alert.accept()
                except NoAlertPresentException:
                    pass
                driver.refresh()
                wait.until(lambda d: bulk_modal.get_title() == "Dashboard")
                continue
                
            except TimeoutException:
                print(f"[WARN] Timeout on attempt {attempt + 1}. Reloading...")
                driver.refresh()
                wait.until(lambda d: bulk_modal.get_title() == "Dashboard")
                continue

        if not success:
            pytest.fail(f"Failed to bulk upload after {max_retries} attempts.")

        # Step 5: ensure domains appear in page source
        wait.until(
            lambda d: all(domain in d.page_source.lower() for domain in domains),
            message="Not all bulk domains appeared in the page source"
        )

        # Step 6: Verify results
        with open(check_domains_json_path, "r") as f:
            check_domains_details_list = json.load(f)

        for domain_to_check in check_domains_details_list:
            target_domain = domain_to_check["domain"]
            target_status = domain_to_check["status"]

            def specific_domain_ready(d):
                try:
                    data = bulk_modal.get_domain_data(domain=target_domain)
                    if data and data["status"] == target_status:
                        return data
                    return False
                except Exception:
                    return False

            print(f"Waiting for domain data: {target_domain}")
            domain_details_dashboard = wait.until(specific_domain_ready)

            assert domain_details_dashboard is not None
            assert domain_details_dashboard["status"] == target_status
            assert domain_details_dashboard["ssl_issuer"].lower() == domain_to_check["ssl_issuer"].lower()
            assert domain_details_dashboard["ssl_expiration"] and domain_details_dashboard["ssl_expiration"] != "None" 

    finally:
        remove_fixed_file_path(
            check_file=check_domains_json_path,
            domains_file=domains_file_path
        )
        
        user_domains_path = os.path.join(USERS_DATA_DIR, "Selenium_Tester_12345_domains.json")
        if os.path.exists(user_domains_path):
            try:
                with open(user_domains_path, "w") as f:
                    json.dump([], f)
            except Exception as e:
                print(f"[WARN] Failed to clean up domains file: {e}")