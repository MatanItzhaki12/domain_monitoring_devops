import os
# from IP_Library import BACKEND_IP, BACKEND_PORT, BACKEND_URL, FRONTEND_IP, FRONTEND_PORT, FRONTEND_URL

BACKEND_IP = os.environ.get(
    "BACKEND_IP", "localhost"
)
BACKEND_PORT = 8080

BACKEND_URL = f"http://{BACKEND_IP}:{BACKEND_PORT}"


FRONTEND_IP = os.environ.get(
    "FRONTEND_IP", "localhost"
)

FRONTEND_PORT = 8081

FRONTEND_URL = f"http://{FRONTEND_IP}:{FRONTEND_PORT}"

DATABASE_IP = os.environ.get(
    "DATABASE_IP", "localhost"
)

DATABASE_PORT = 5432

DATABASE_URL = f"http://{DATABASE_IP}:{DATABASE_PORT}"
DATABASE_USER = os.environ.get(
    "DATABASE_USER", "user"
)
DATABASE_PASSWORD = os.environ.get(
    "DATABASE_PASSWORD", "password"
)