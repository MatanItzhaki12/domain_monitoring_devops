import os
import random
import string
import json


def random_domain():
    return f"{''.join(random.choices(string.ascii_lowercase, k=8))}.com"


def generate_domain_file(directory, count=5):
    domains = [random_domain() for _ in range(count)]
    file_path = os.path.join(directory, "test_domains.txt")

    with open(file_path, "w") as f:
        f.write("\n".join(domains))

    return file_path, domains

def generate_fixed_domain_file(directory):
    domains_details = [
        {
            "domain": "apple.com",
            "status": "Live",
            "ssl_expiration": "2025-12-17",
            "ssl_issuer": "Apple Inc."
        },
        {
            "domain": "google.com",
            "status": "Live",
            "ssl_expiration": "2026-01-19",
            "ssl_issuer": "Google Trust Services"   
        },
        {
            "domain": "google.fyi",
            "status": "Down",
            "ssl_expiration": "N/A",
            "ssl_issuer": "N/A"
        },
        {
            "domain": "httpforever.com",
            "status": "Live",
            "ssl_expiration": "N/A",
            "ssl_issuer": "N/A"
        }
    ]
    domains = [
        "apple.com",
        "google.com",
        "google.fyi",
        "httpforever.com"
    ]
    # Creating domains' file
    domains_file_path = os.path.join(directory, "test_fixed_domains.txt")
    domains_file_path = os.path.abspath(domains_file_path) 
    with open(domains_file_path, "w") as f:
        f.write("\n".join(domains))

    # Creating check domains' file
    check_domains_file_path = os.path.join(directory, "check_fixed_domains.txt")
    check_domains_file_path = os.path.abspath(check_domains_file_path) 
    with open(check_domains_file_path, "w") as f:
        json.dump(domains_details, f)

    return domains_file_path, check_domains_file_path, domains

def remove_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def remove_fixed_file_path(check_file, domains_file):
    remove_file(check_file)
    remove_file(domains_file)
