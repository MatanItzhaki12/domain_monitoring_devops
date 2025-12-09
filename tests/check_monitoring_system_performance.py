import time
import sys
import os

# The correct path for the modules
module_path = os.path.abspath(".") 
if module_path not in sys.path:
    sys.path.append(module_path)

from MonitoringSystem import MonitoringSystem as MS
from DomainManagementEngine import DomainManagementEngine as DME



# Initializing Domain Management Engine and Monitoring System
dme = DME()
ms = MS()

# Preparing users and users file for checking
users = [f"test{i}" for i in range(1,12)]

# users_domains = {}
# for user in users: 
#     users_domains[user] = dme.load_user_domains(user)
# # [print(domain) for domain in users_domains[user]]

# performing checks
for user in users:
    start = time.time()

    ms.scan_user_domains(username=user, dme=dme)
    end = time.time()
    print(f"{user}'s domains check ended in {end-start:.2f} Seconds.")