
import requests

import ssl
import socket
from datetime import datetime, timezone
import json
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

class 
def check_status(domain):
    try:    
        response = requests.get(domain, timeout=5)
        print("status code is:", response.status_code)
    except requests.exeptions.RequestException as e:
        print("Error:", e)

check_status("")

def check_ssl(domain):
    try: 

        context = ssl.create_defult_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                certificate = ssock.getpeercert()
        
        expired_str = certificate['notAfter']
        expire_date = datetime.strptime(expired_str, "%b %d")

        if expire_date > datetime.new():
            print(f"SSL for {domain} is VALID until {expire_date}")
        else:
            print(f"SSL for {domain} is EXPIRED on {expire_date}")

    except Exception as e:
        print(f"there is ERROR checking SSL for {domain}: {e}")

check_ssl("")


