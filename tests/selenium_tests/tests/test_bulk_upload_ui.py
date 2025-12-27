import pytest
import os
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException, TimeoutException, NoAlertPresentException

from tests.selenium_tests.pages.login_page import LoginPage
from tests.selenium_tests.pages.bulk_upload_modal import BulkUploadModal
from tests.selenium_tests.utils.domain_factory import generate_fixed_domain_file, remove_fixed_file_path

pytestmark = pytest.mark.order(10)

# Directory of this test file
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
# Temp directory inside the test folder
TEMP_DIR = os.path.join(TEST_DIR, "selenium_temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Helper to find project root for robust cleanup (fixes FileNotFoundError)
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, "..", "..", ".."))
USERS_DATA_DIR = os.path.join(PROJECT_ROOT, "UsersData")

def test_1_bulk_upload_ui(driver, base_url):
    # Setup explicit wait (25 seconds)
    wait = WebDriverWait(driver, 25)

    # ----------------------------------------------------
    # 1. LOGIN STEPS (Restored)
    # ----------------------------------------------------
    login_page = LoginPage(driver, base_url)
    login_page.load()
    login_page.login("Selenium_Tester_12345", "St87654321")
    
    # REPLACED sleep(1): Wait for the dashboard URL to confirm login success
    wait.until(EC.url_contains("/dashboard"))

    # Optional: Clear any leftover alerts (like "Scan failed") from previous runs
    try:
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
    except (TimeoutException, NoAlertPresentException):
        pass

    # ----------------------------------------------------
    # 2. DASHBOARD LOAD
    # ----------------------------------------------------
    bulk_modal = BulkUploadModal(driver=driver, base_url=base_url)
    bulk_modal.load()
    
    # REPLACED sleep(1): Wait for Dashboard title
    wait.until(lambda d: bulk_modal.get_title() == "Dashboard")
    
    # REPLACED sleep(1): Wait for Welcome Message
    wait.until(lambda d: "Selenium_Tester_12345" in bulk_modal.get_welcome_message())

    # =========================
    #  BULK UPLOAD TEST
    # =========================

    # Step 1: open modal
    bulk_modal.open_bulk_upload()
    # REPLACED sleep(0.5): Implicit wait handles the next interaction

    # Step 2: create domain file
    domains_file_path, check_domains_json_path, domains = generate_fixed_domain_file(TEMP_DIR)

    try:
        # Step 3: upload file
        bulk_modal.upload_bulk(file_path=domains_file_path)
        
        # REPLACED assertion: Wait for the success status text to appear
        wait.until(lambda d: bulk_modal.get_final_status() == "Bulk upload completed!")
        
        # Step 4: wait until dashboard is active again
        bulk_modal.wait_for_active_dashboard()

        # Step 5: ensure domains appear in page source
        # REPLACED sleep(5): Wait dynamically until ALL domains are present in DOM
        wait.until(
            lambda d: all(domain in d.page_source.lower() for domain in domains),
            message="Not all bulk domains appeared in the page source"
        )

        # Step 6: Verify results
        with open(check_domains_json_path, "r") as f:
            check_domains_details_list = json.load(f)

        # REPLACED sleep(2) loop: Iterate and wait for EACH specific row to be ready
        for domain_to_check in check_domains_details_list:
            target_domain = domain_to_check["domain"]
            target_status = domain_to_check["status"]

            # Define a helper to wait for this specific domain's data
            def specific_domain_ready(d):
                try:
                    data = bulk_modal.get_domain_data(domain=target_domain)
                    # Ensure data exists AND status matches (handles "Scanning" -> "Live" transition)
                    if data and data["status"] == target_status:
                        return data
                    return False
                except Exception:
                    return False

            print(f"Waiting for domain data: {target_domain}")
            
            # Smart wait for the specific row data
            domain_details_dashboard = wait.until(specific_domain_ready)

            print(domain_details_dashboard)
            # Validate results
            assert domain_details_dashboard is not None
            assert domain_details_dashboard["status"] == target_status
            assert domain_details_dashboard["ssl_issuer"].lower() == domain_to_check["ssl_issuer"].lower()
            assert domain_details_dashboard["ssl_expiration"] and domain_details_dashboard["ssl_expiration"] != "None" 

    except UnexpectedAlertPresentException as e:
        # Handle "Scan failed" alert if it appears
        try:
            alert = driver.switch_to.alert
            text = alert.text
            alert.accept()
            pytest.fail(f"Test failed due to unexpected browser alert: '{text}'")
        except Exception:
            pytest.fail(f"Test failed due to unexpected alert: {e}")

    finally:
        # CLEANUP
        remove_fixed_file_path(
            check_file=check_domains_json_path,
            domains_file=domains_file_path
        )
        
        # Clean User Domain (Using fixed absolute path)
        user_domains_path = os.path.join(USERS_DATA_DIR, "Selenium_Tester_12345_domains.json")
        if os.path.exists(user_domains_path):
            try:
                with open(user_domains_path, "w") as f:
                    json.dump([], f)
            except Exception as e:
                print(f"[WARN] Failed to clean up domains file: {e}")