from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, Tuple, Any, Optional
from logger import setup_logger

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
    [
        {
          "host": "example.com",
          "added_at": "2025-09-15T12:34:56.000Z",
          "last_check": "2025-09-15T14:10:40.000Z",
          "http": null,
          "ssl":  null
        }
    ]
    
    """

    # Regex for FQDN validation (example.com, sub.example.co.il etc.)
    _FQDN_RE = re.compile(
        r"^(?=.{1,253}$)(?!-)([A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$"
    )

    def __init__(self):
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

    def load_user_domains(self, username: str) -> List[Dict[str, Any]]:
        """
        Load (or initialize) user's domain list.
        The JSON file contains only a list of domain objects.
        """
        path = _domains_path(username)
        with _lock:
            if not os.path.exists(path):
                os.makedirs(USERS_DATA_DIR, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                return []

            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []
            return sorted(data, key=lambda x: x["domain"].lower())


    def save_user_domains(self, username: str, data: List[Dict[str, Any]]) -> None:
        """Save user's domain list to disk."""
        path = _domains_path(username)
        with _lock:
            os.makedirs(USERS_DATA_DIR, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(sorted(data, key=lambda x: x["domain"].lower()), 
                          f, ensure_ascii=False, indent=2)

    def list_domains(self, username: str) -> List[Dict[str, Any]]:
        return self.load_user_domains(username)

    def set_last_full_check_now(self, username: str) -> None:
        """Update last full check timestamp (to be called after MonitoringSystem run)."""
        with _lock:
            data = self.load_user_domains(username)
            data["last_full_check"] = _utc_now_iso()
            self.save_user_domains(username, data)

    def add_domain(self, username: str, raw_domain: str) -> bool:
        ok, host, reason = self.validate_domain(raw_domain)
        if not ok or not host:
            return False

        with _lock:
            domains = self.load_user_domains(username)
            existing = {d.get("domain") for d in domains}
            if host in existing:
                return False

            domains.append({
                "domain": host,
                "status": "Pending",
                "ssl_expiration": "N/A",
                "ssl_issuer": "N/A"
            })

            self.save_user_domains(username, domains)
            return True


    def bulk_upload(self, username: str, file_path: str) -> Dict[str, Any]:
        """
        Bulk upload domains from a text file.
        Each valid line is added as:
        {
            "domain": "<domain>",
            "status": "Pending",
            "ssl_expiration": "N/A",
            "ssl_issuer": "N/A"
        }
        Returns a summary dict.
        """
        logger = setup_logger("bulk_upload")

        if not os.path.exists(file_path):
            logger.error(f"Bulk upload failed: file not found -> {file_path}")
            return {"ok": False, "error": "File not found"}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                domains_to_add = [line.strip().lower() for line in f if line.strip()]
        except Exception as e:
            logger.exception(f"Failed to read bulk upload file: {e}")
            return {"ok": False, "error": "Could not read file"}

        if not domains_to_add:
            return {"ok": False, "error": "File is empty or invalid"}

        added, duplicates, invalid = [], [], []

        with _lock:
            domains = self.load_user_domains(username)
            existing = {d.get("domain") for d in domains}

            for raw in domains_to_add:
                ok, normalized, reason = self.validate_domain(raw)
                if not ok or not normalized:
                    logger.warning(f"Invalid domain skipped: {raw} ({reason})")
                    invalid.append({"input": raw, "reason": reason})
                    continue

                if normalized in existing:
                    logger.warning(f"Duplicate domain skipped: {normalized}")
                    duplicates.append(normalized)
                    continue

                domains.append({
                    "domain": normalized,
                    "status": "Pending",
                    "ssl_expiration": "N/A",
                    "ssl_issuer": "N/A"
                })
                added.append(normalized)
                existing.add(normalized)

            self.save_user_domains(username, domains)

        summary = {
            "ok": True,
            "summary": {
                "added": added,
                "duplicates": duplicates,
                "invalid": invalid
            }
        }
        logger.info(f"Bulk upload summary for {username}: {summary}")
        return summary

    def remove_domains(self, username: str, hosts: List[str]) -> Dict[str, List[str]]:
        """
        Remove domains from the user's list.
        :param hosts: list of domain strings
        :return: {"removed": [...], "not_found": [...]}
        """
        to_remove = {self._normalize_domain(h) for h in (hosts or []) if h and h.strip()}
        to_remove.discard("")

        removed, not_found = [], []

        with _lock:
            domains = self.load_user_domains(username)
            current = {d.get("domain") for d in domains}

            # Remove matching entries
            new_list = [d for d in domains if d.get("domain") not in to_remove]
            removed = list(current.intersection(to_remove))

            # Track domains that didn't exist
            not_found = list(to_remove - current)

            self.save_user_domains(username, new_list)

        return {"removed": removed, "not_found": not_found}

    
