import time
from selenium.webdriver.common.by import By
from tests.selenium_tests.pages.base_page import BasePage
from selenium.webdriver.support import expected_conditions as EC

class DashboardPage(BasePage):
    PATH = f"/dashboard"
    # Locators:
    welcome_message = (By.ID, "greeting")
    logout_button = (By.ID, "logoutBtn")
    scan_now_button = (By.ID, "scanNowBtn")
    table_rows = (By.CSS_SELECTOR, "table tbody tr")
    row_data = (By.TAG_NAME, "td")
    add_domain_button = (By.ID, "openAddDomain")
    
    # Actions:   
    def get_welcome_message(self):
        return self.get_text(locator=self.welcome_message)
    
    def wait_for_active_dashboard(self):
        self.wait.until(EC.element_to_be_clickable(self.add_domain_button))

    def logout(self):
        time.sleep(0.5)
        self.click(locator=self.logout_button)
        time.sleep(1)

    def scan_now(self):
        self.click(locator=self.scan_now_button)

    def get_table_rows(self):
        return self.wait_for_multiple_elements(self.table_rows)

    def get_row_columns(self, row):
        return self.wait.until(
            lambda driver: row.find_elements(*self.row_data)
        )

    def get_domain_data(self, domain):
        rows = self.get_table_rows()
        for row in rows:
            columns = self.get_row_columns(row)
            # Skip for empty column or invalid column
            if not columns or len(columns) != 6:
                continue
            # Extract Domain from row
            row_domain = columns[1].text.strip()
            # Check for specific domain
            if row_domain == domain:
                return {
                    "domain": row_domain,
                    "status": columns[2].text.strip(),
                    "ssl_expiration": columns[3].text.strip(),
                    "ssl_issuer": columns[4].text.strip()
                }

        return None
    
    def get_all_domains_data(self):
        domains_list = []
        rows = self.get_table_rows()
        for row in rows:
            columns = self.get_row_columns(row)
            # Skip for empty column or invalid column
            if not columns or len(columns)!=6:
                continue
            # Extract Domain from row
            row_domain = columns[1].text.strip()
            row_status = columns[2].text.strip()
            row_ssl_exp = columns[3].text.strip()
            row_ssl_issuer = columns[4].text.strip()
            # Check for specific domain
            domains_list.append( {
                    "domain": row_domain,
                    "status": row_status,
                    "ssl_expiration": row_ssl_exp,
                    "ssl_issuer": row_ssl_issuer
                } )

        return domains_list
