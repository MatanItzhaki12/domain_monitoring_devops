from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, Tuple, Any, Optional

# ----------------------------
# Thread-safety for file IO
# ----------------------------
_lock = RLock()

# ----------------------------
# Base directory for per-user JSON files
# ----------------------------
BASE_DIR = os.path.dirname(__file__)
USERS_DATA_DIR = os.path.join(BASE_DIR, "UsersData")


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 with 'Z' suffix."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _domains_path(username: str) -> str:
    """Generate per-user JSON file path."""
    safe_user = re.sub(r"[^A-Za-z0-9_.-]", "_", username.strip())
    return os.path.join(USERS_DATA_DIR, f"{safe_user}_domains.json")


class DomainManagementEngine:
    """
    File-backed user domain storage and domain validation/CRUD.

    JSON structure example (UsersData/alex_domains.json):
    {
      "username": "alex",
      "last_full_check": "2025-09-15T14:10:43.201Z",
      "domains": [
        {
          "host": "example.com",
          "added_at": "2025-09-15T12:34:56.000Z",
          "last_check": "2025-09-15T14:10:40.000Z",
          "http": null,
          "ssl":  null
        }
      ]
    }
    """

    # Regex for FQDN validation (example.com, sub.example.co.il etc.)
    _FQDN_RE = re.compile(
        r"^(?=.{1,253}$)(?!-)([A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$"
    )

    def __init__(self, user_manager: Optional[object] = None):
        """
        :param user_manager: Optional UserManager object for integration with user logic
        """
        self.user_manager = user_manager
        os.makedirs(USERS_DATA_DIR, exist_ok=True)

    @staticmethod
    def _normalize_domain(raw: str) -> str:
        """Normalize domain: remove scheme, trim slashes, lowercase, remove port and trailing dot."""
        if not raw:
            return ""
        s = raw.strip().lower()

        if s.startswith("http://"):
            s = s[7:]
        elif s.startswith("https://"):
            s = s[8:]

        s = s.split("/", 1)[0]
        s = s.split("?", 1)[0]
        s = s.split("#", 1)[0]

        if ":" in s:
            s = s.split(":", 1)[0]

        if s.endswith("."):
            s = s[:-1]

        return s

    def validate_domain(self, raw_domain: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate domain format.
        :return: (ok, normalized_host|None, reason|None)
        """
        host = self._normalize_domain(raw_domain)
        if not host:
            return False, None, "Empty domain"

        if not self._FQDN_RE.match(host):
            return False, None, "Domain does not match FQDN format"

        return True, host, None

    @staticmethod
    def _empty_user_doc(username: str) -> Dict[str, Any]:
        """Return a fresh user document structure."""
        return {"username": username, "domains": []}

    def load_user_domains(self, username: str) -> Dict[str, Any]:
        """
        Load (or initialize) user's domain JSON.
        Always returns dict with: username, domains[, last_full_check].
        """
        path = _domains_path(username)
        with _lock:
            if not os.path.exists(path):
                os.makedirs(USERS_DATA_DIR, exist_ok=True)
                doc = self._empty_user_doc(username)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(doc, f, ensure_ascii=False, indent=2)
                return doc

            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = self._empty_user_doc(username)

            data.setdefault("username", username)
            data.setdefault("domains", [])
            return data

    def save_user_domains(self, username: str, data: Dict[str, Any]) -> None:
        """Save user's domain JSON to disk."""
        path = _domains_path(username)
        with _lock:
            os.makedirs(USERS_DATA_DIR, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def list_domains(self, username: str) -> Dict[str, Any]:
        """Return user document with username, domains[, last_full_check]."""
        return self.load_user_domains(username)

    def set_last_full_check_now(self, username: str) -> None:
        """Update last full check timestamp (to be called after MonitoringSystem run)."""
        with _lock:
            data = self.load_user_domains(username)
            data["last_full_check"] = _utc_now_iso()
            self.save_user_domains(username, data)

    def add_domain(self, username: str, raw_domain: str) -> bool:
        """
        Add domain to user's list.
        :return: True if new domain added, False if domain already exists or invalid.
        """
        ok, host, reason = self.validate_domain(raw_domain)
        if not ok or not host:
            return False

        with _lock:
            data = self.load_user_domains(username)
            existing = {d.get("host") for d in data.get("domains", [])}
            if host in existing:
                return False

            data["domains"].append(
                {
                    "host": host,
                    "added_at": _utc_now_iso(),
                    "last_check": None,
                    "http": None,
                    "ssl": None,
                }
            )
            self.save_user_domains(username, data)
            return True

    def remove_domains(self, username: str, hosts: List[str]) -> Dict[str, List[str]]:
        """
        Remove domains from user's list.
        :param hosts: list of raw domain strings
        :return: {"removed": [...], "not_found": [...]}
        """
        to_remove = {self._normalize_domain(h) for h in (hosts or []) if h and h.strip()}
        to_remove.discard("")

        removed: List[str] = []
        not_found: List[str] = []

        with _lock:
            data = self.load_user_domains(username)
            new_list = []
            current = {d.get("host") for d in data.get("domains", [])}

            for entry in data.get("domains", []):
                host = entry.get("host")
                if host in to_remove:
                    removed.append(host)
                else:
                    new_list.append(entry)

            for h in to_remove:
                if h not in current:
                    not_found.append(h)

            data["domains"] = new_list
            self.save_user_domains(username, data)

        return {"removed": removed, "not_found": not_found}
