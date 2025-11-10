import socket
import ssl
import concurrent.futures
from datetime import datetime, timezone
<<<<<<< HEAD
import json
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import logger

logger = logger.setup_logger("MonitoringSystem")

class MonitoringSystem:

    def liveness_check(self, domain):
        logger.info(f'Getting status code for {domain}')
        try:
            domain_clean = domain.replace("https://", "").replace("http://", "")\
                            .replace("www.", "").split("/")[0]
            response = requests.get(f'http://{domain_clean}', timeout=5)
            if not response.ok:
                response = requests.get(f'https://{domain_clean}', timeout=5)
                if not response.ok:
                     return "Down"
            return "Live"
        except requests.exceptions.RequestException:
            logger.error(f'Could not get the status code for {self.domain}')
            return "Down"    

    def ssl_check(self, domain):
        logger.info(f'Getting certificate information for {domain}')
        cert_info = { 'ssl_issuer': 'N/A', 'expiration_date': 'N/A'}
        try:
            domain_clean = domain.replace("https://", "").replace("http://", "")\
                            .replace("www.", "").split("/")[0]
            context = ssl.create_default_context()
            with socket.create_connection((domain_clean, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=domain_clean) as ssock:
                    cert = ssock.getpeercert()
            if not cert or "notAfter" not in cert:
                logger.debug(f'Could not find certificate information for {domain_clean}')
                return cert_info
            issuer_dict = { key:value for tupl in cert['issuer'] for key, value in tupl }
            cert_info['ssl_issuer'] = issuer_dict.get("organizationName", "N/A")
            cert_info['expiration_date'] = datetime.strptime(cert['notAfter'], "%Y-%m-%d")
            return cert_info
        except Exception as e:
            logger.error(f'Could not get the certificate information for {domain}')
            return cert_info

    def get_domain_info(self, domain):
        logger.info(f'Getting information for {domain}')
        domain_info = {
            "domain": f"{domain}",
            "status": "Pending",
            "ssl_expiration": "N/A",
            "ssl_issuer": "N/A"
        }
        try:
            liveness = self.liveness_check(domain)
            domain_info["status"] = liveness
            if liveness == "Live":
                ssl_info = self.ssl_check(domain)
                domain_info["ssl_issuer"] = ssl_info["ssl_issuer"]
                domain_info["ssl_expiration"] = ssl_info["ssl_expiration"]
            return domain_info
        except Exception as e:
            logger.info(f'Could not get information for {domain}')
            return domain_info         

    def check_user_domains_info(self, username, user_domains):
        logger.info(f'Getting information for all {username}\'s domains.')
        try:
            new_domains_info = []
            for domain_details in user_domains:
                new_domains_info.append(self.get_domain_info(domain_details["domain"]))
            return new_domains_info            
        except:
            logger.info(f'Could not get information for {username}\'s domains.')    
            return None

    def check_all_users_domains(self, users_domains):
        logger.info(f'Getting information for all users\' domains.')
        try:
            for username in users_domains:
                new_domains_info = self.check_user_domains_info(username, users_domains[username])
                if not new_domains_info:
                    new_domains_info = {
                        "domain": users_domains["domain"],
                        "status": "Pending",
                        "ssl_expiration": "N/A",
                        "ssl_issuer": "N/A"
                    }
                users_domains[username] = new_domains_info
        except Exception as e:
            logger.info(f'Could not get information for all users\' domains.')

    def check_status(domain):
        try:    
            response = requests.get(domain, timeout=5)
            print("Status Code is:", response.status_code)
        except  requests.exceptions.RequestException as e:
                print("Error:", e)

    check_status("https://google.com")

    def check_ssl(domain):
        try: 

            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    certificate = ssock.getpeercert()
            
            expired_str = certificate['notAfter']
            expire_date = datetime.strptime(expired_str, "%b %d %H:%M:%S %Y %Z")

            if expire_date > datetime.now():
                print(f"SSL for {domain} is VALID till {expire_date}")
            else:
                print(f"SSL for {domain} will EXPIRED on {expire_date}")

        except Exception as e:
                print(f"There is an ERROR checking SSL for {domain}: {e}")

    check_ssl("google.com")
=======
from typing import Dict, Any, List
from logger import setup_logger
from DomainManagementEngine import DomainManagementEngine

logger = setup_logger("MonitoringSystem")

SSL_CTX = ssl.create_default_context()

class MonitoringSystem:
    @staticmethod
    def _check_domain(domain: str) -> Dict[str, Any]:
        """
        Check reachability and SSL certificate details using sockets.
        Falls back to HTTP port 80 if SSL is unavailable.
        Returns: Live / Expired SSL / Down
        """
        result = {
            "domain": domain,
            "status": "Down",
            "ssl_expiration": "N/A",
            "ssl_issuer": "N/A"
        }

        # Normalize host
        host = domain.lower().strip().replace("http://", "").replace("https://", "").split("/")[0]

        # DNS Check - no need to check further if the dns did not resolve the ip
        try:
            ip = socket.gethostbyname(host)
        except Exception as e:
            logger.warning(f"DNS failed to resolve the domain: {domain}")
            return result

        # --- Try HTTPS first ---
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                if sock.connect_ex((host, 443)) == 0:
                    with SSL_CTX.wrap_socket(sock, server_hostname=host) as ssock:
                        cert = ssock.getpeercert()

                        expiry_str = cert.get("notAfter")
                        if expiry_str:
                            expiry_date = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z").replace(
                                tzinfo=timezone.utc
                            )
                            result["ssl_expiration"] = expiry_date.strftime("%Y-%m-%d")

                            result["status"] = "Live"

                        issuer = next(
                            (v for tup in cert.get("issuer", []) for k, v in tup if k == "organizationName"),
                            None
                        )
                        result["ssl_issuer"] = issuer or "Unknown"

                        return result 
                else:
                    logger.debug(f"HTTPS connection is unavailable for {domain}")

        except (socket.timeout, ssl.SSLError) as e:
            logger.warning(f"HTTPS failed for {domain}: {e}")
        except Exception as e:
            logger.error(f"HTTPS Error for {domain}: {e}")

        # --- Fallback: try HTTP port 80 ---
        try:   
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                if sock.connect_ex((host, 80)) == 0:
                    http_request = f"HEAD / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
                    sock.sendall(http_request.encode())
                    response = sock.recv(512).decode(errors="ignore")

                    if "HTTP" in response:
                        result["status"] = "Live"
                    else:
                        result["status"] = "Down"
                else:
                    logger.debug(f"HTTP connection is unavailable for {domain}")

        except socket.timeout:
            logger.warning(f"Timeout while checking HTTP for {domain}")
        except Exception as e:
            logger.warning(f"HTTP fallback failed for {domain}: {e}")

        return result


    @staticmethod
    def scan_user_domains(username: str, dme: DomainManagementEngine, max_workers: int = 50) -> List[Dict[str, Any]]:
        """
        Run SSL and reachability checks for all domains concurrently.
        """
        domains = dme.load_user_domains(username)
        if not domains:
            logger.info(f"No domains found for user {username}")
            return []
>>>>>>> main

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(MonitoringSystem._check_domain, d["domain"]): d for d in domains}
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Domain check failed in worker: {e}")

        dme.save_user_domains(username, results)
        logger.info(f"{len(results)} domains scanned for {username}")
        return results
