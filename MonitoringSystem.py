# MonitoringSystem.py
import ssl
import socket
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from DomainManagementEngine import DomainManagementEngine as DME

# Logging (uses your existing logger if available)
try:
    import logger
    log = logger.setup_logger("MonitoringSystem")
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("MonitoringSystem")

# ------------------------------
# SETTINGS
# ------------------------------
MAX_THREADS = 30                 # concurrent threads
CONNECT_TIMEOUT = 1.5
READ_TIMEOUT = 2.0
SOCKET_TIMEOUT = 3.0
REQUEST_TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)
BATCH_SIZE = 10                  # flush results every 10 domains
FLUSH_INTERVAL = 2.0             # or every 2 seconds
USER_AGENT = "DomainChecker/1.1"

# ------------------------------
# GLOBAL HTTP SESSION
# ------------------------------
def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    retries = Retry(
        total=1,
        backoff_factor=0.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(pool_connections=64, pool_maxsize=64, max_retries=retries)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

_session = _make_session()

# ------------------------------
# HELPERS
# ------------------------------
def _clean_host(domain: str) -> str:
    if not domain:
        return ""
    s = domain.strip().lower()
    if s.startswith("http://"):
        s = s[7:]
    elif s.startswith("https://"):
        s = s[8:]
    s = s.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    if ":" in s:
        s = s.split(":", 1)[0]
    if s.endswith("."):
        s = s[:-1]
    return s

def _can_resolve_fast(host: str) -> bool:
    """Fast DNS check — skip host if cannot resolve quickly."""
    try:
        socket.getaddrinfo(host, 80, type=socket.SOCK_STREAM)
        return True
    except socket.gaierror:
        return False

def _is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def _check_status(host: str) -> str:
    """Try HTTPS first, then HTTP. Return Live/Down."""
    for scheme in ("https://", "http://"):
        try:
            r = _session.get(f"{scheme}{host}", timeout=REQUEST_TIMEOUT, allow_redirects=False)
            if 200 <= r.status_code < 400:
                return "Live"
        except requests.exceptions.RequestException:
            continue
    return "Down"

def _check_ssl(host: str) -> tuple[str, str]:
    """Check SSL expiration and issuer quickly."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=SOCKET_TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        not_after = cert.get("notAfter")
        if not not_after:
            return "N/A", "N/A"
        expire_dt = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
        expire_str = expire_dt.strftime("%Y-%m-%d")
        issuer = dict(x[0] for x in cert.get("issuer", [] )).get("organizationName", "Unknown")
        return expire_str, issuer
    except Exception:
        return "N/A", "N/A"

def _scan_one(host: str) -> tuple[str, dict]:
    """Check single host with DNS and port filtering."""
    if not _can_resolve_fast(host):
        return host, {"status": "Down", "ssl_expiration": "N/A", "ssl_issuer": "N/A"}

    status = _check_status(host)
    ssl_expiration, ssl_issuer = ("N/A", "N/A")
    if status == "Live" or _is_port_open(host, 443, timeout=1.0):
        ssl_expiration, ssl_issuer = _check_ssl(host)

    return host, {
        "status": status,
        "ssl_expiration": ssl_expiration,
        "ssl_issuer": ssl_issuer
    }

# ------------------------------
# MAIN FUNCTIONALITY
# ------------------------------
def run_user_check(username: str) -> dict:
    """Run domain checks for user with incremental updates."""
    dme = DME()
    domains_data = dme.list_domains(username)
    hosts = [_clean_host(d.get("domain", "")) for d in domains_data if d.get("domain")]

    if not hosts:
        log.info(f"[{username}] No domains to scan.")
        return {"ok": True, "domains": 0, "updated": 0}

    updates = {}
    errors = 0
    last_flush = time()

    log.info(f"[{username}] Starting scan of {len(hosts)} domains using {MAX_THREADS} threads...")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(_scan_one, h) for h in hosts]
        for fut in as_completed(futures):
            try:
                host, fields = fut.result()
                updates[host] = fields
            except Exception as e:
                errors += 1
                log.error(f"[{username}] Error: {e}")
                continue

            # Incremental flush every BATCH_SIZE or FLUSH_INTERVAL seconds
            if len(updates) >= BATCH_SIZE or (time() - last_flush >= FLUSH_INTERVAL):
                dme.update_fields(username, updates)
                updates = {}
                last_flush = time()

        # Final flush
        if updates:
            dme.update_fields(username, updates)

    log.info(f"[{username}] Scan complete. Errors={errors}")
    return {"ok": True, "domains": len(hosts), "errors": errors}

def run_user_check_async(username: str) -> None:
    """Start background scan in daemon thread (used by app.py)."""
    def _worker():
        try:
            run_user_check(username)
        except Exception as e:
            log.exception(f"[{username}] Background scan failed: {e}")

    threading.Thread(target=_worker, name=f"scan-{username}", daemon=True).start()
