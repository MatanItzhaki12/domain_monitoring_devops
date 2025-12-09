import os
import time
import random
import string
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


WAIT_TIMEOUT = 10


def generate_random_domains(count=5):
    """Create N random domains like abcd1234.com"""
    def rnd():
        return f"{''.join(random.choices(string.ascii_lowercase, k=8))}.com"
    return [rnd() for _ in range(count)]


def add_bulk_domains(driver):
    """Perform bulk upload of random domains using the modal."""

    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    # --- Step 1: Generate and write random domains file ---
    domains = generate_random_domains()
    file_path = os.path.join(os.path.dirname(__file__), "test_domains.txt")

    with open(file_path, "w") as f:
        f.write("\n".join(domains))

    print(f"[INFO] Random bulk domains created: {domains}")

    # --- Step 2: Ensure dashboard is loaded ---
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # --- Step 3: Open the Bulk Upload modal ---
    bulk_btn = wait.until(EC.element_to_be_clickable((By.ID, "openBulkUpload")))
    bulk_btn.click()
    print("[INFO] Bulk upload modal opened.")

    time.sleep(0.5) 

    # --- Step 4: Upload the file ---
    file_input = driver.find_element(By.CSS_SELECTOR, "#bulkUploadForm input[type='file']")
    file_input.send_keys(file_path)
    assert file_input.get_attribute("value"), "File selection failed."

    # --- Step 5: Submit via JS (same as UI) ---
    time.sleep(0.5)  
    driver.execute_script(
        "document.getElementById('bulkUploadForm').dispatchEvent(new Event('submit', { bubbles: true }));"
    )
    print("[INFO] Bulk upload form submitted.")

    # --- Step 6: Verify domains appear ---
    time.sleep(4)  
    driver.get(driver.current_url)  
    page_source = driver.page_source.lower()

    for d in domains:
        assert d in page_source, f"Domain missing from dashboard: {d}"

    print(f"[OK] All uploaded domains appear on dashboard: {domains}")

    # --- Cleanup ---
    if os.path.exists(file_path):
        os.remove(file_path)

    return domains
