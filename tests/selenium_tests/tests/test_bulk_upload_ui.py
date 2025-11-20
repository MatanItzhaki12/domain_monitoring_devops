import tempfile
import pytest
import time
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from tests.selenium_tests.pages.login_page import LoginPage
from tests.selenium_tests.pages.bulk_upload_modal import BulkUploadModal
from tests.selenium_tests.utils.domain_factory import generate_fixed_domain_file, remove_fixed_file_path

pytestmark = pytest.mark.order(10)

# Get temp directory
TEMP_DIR = tempfile.gettempdir()


def test_1_bulk_upload_ui(driver, base_url):
    login_page = LoginPage(driver, base_url)
    login_page.load()
    login_page.login("Selenium_Tester_12345", "St87654321")
    time.sleep(1)
    # Wait until dashboard loads
    bulk_modal = BulkUploadModal(driver=driver, base_url=base_url)
    bulk_modal.load()
    time.sleep(1)
    #dashboard.wait_for(locator=dashboard.welcome_message)
    assert bulk_modal.get_title() == "Dashboard"
    # bulk_upload_modal inherit from DashboardPage
    assert "Selenium_Tester_12345" in bulk_modal.get_welcome_message()
    time.sleep(1)

    # =========================
    #  BULK UPLOAD TEST
    # =========================

    # Step 1: open modal

    # dashboard.open_bulk_upload()
    bulk_modal.open_bulk_upload()
    time.sleep(0.5)
    
    # Step 2: create domain file
    domains_file_path, check_domains_json_path, domains = generate_fixed_domain_file(TEMP_DIR)

    # Step 3: upload file
    bulk_modal.upload_bulk(file_path=domains_file_path)
    assert bulk_modal.get_final_status() == "Bulk upload completed!"
    
    # Step 4: wait until dashboard is active again
    bulk_modal.wait_for_active_dashboard()
    # bulk_modal.wait.until(
    #     EC.element_to_be_clickable((By.ID, "openAddDomain"))
    # )
    time.sleep(5)
    # Step 5: ensure domains appear in page source
    assert bulk_modal.wait.until(
        lambda d: all(domain in d.page_source.lower() for domain in domains)
    ), "Not all domains are present on the page"

    # Step 6: Verify results
    # Load JSON file with the correct details 
    with open(check_domains_json_path, "r") as f:
        check_domains_details_list = json.load(f)
    # Iterate through all domains in file, and validate:
    for domain_to_check in check_domains_details_list:
        print(domain_to_check)
        domain_details_dashboard = bulk_modal.get_domain_data(domain=domain_to_check["domain"])
        print(domain_details_dashboard)
        # Validate domain exists
        assert domain_details_dashboard is not None
        # Validate status
        assert domain_details_dashboard["status"] == domain_to_check["status"]
        # Validate SSL issuer
        assert domain_details_dashboard["ssl_issuer"].lower() == domain_to_check["ssl_issuer"].lower()
        # Validate Expiration - only not empty
        assert domain_details_dashboard["ssl_expiration"] and domain_details_dashboard["ssl_expiration"] != "None" 

    # print("[OK] Bulk upload UI test passed.")

    # CLEANUP
    remove_fixed_file_path(
        check_file=check_domains_json_path,
        domains_file=domains_file_path
    )
    # Clean User Domain
    user_domains_path = "./UsersData/Selenium_Tester_12345_domains.json"
    with open(user_domains_path, "w") as f:
        json.dump([], f)
