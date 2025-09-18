from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, Tuple, Any

# Thread-safety for file IO
_lock = RLock()

# Base directory for per-user JSON files
USERS_DATA_DIR = os.path.join(os.path.dirname(__file__), "UsersData")


def _now_iso() -> str:
    """Return current time in ISO 8601 (UTC)."""
    return datetime.now(timezone.utc).isoformat()


def _safe_username(username: str) -> str:
    """
    Sanitize username for filesystem usage.
    Allows alphanumerics, '-' and '_'.
    """
    return "".join(c for c in (username or "") if c.isalnum() or c in ("-", "_"))


def _domains_path(username: str) -> str:
    """
    Build an absolute path to the user's domains file.
    Example: UsersData/<username>_domains.json
    """
    safe = _safe_username(username)
    return os.path.join(USERS_DATA_DIR, f"{safe}_domains.json")


class UserManager:
    """
    File-backed user domain storage and basic domain validation.

    JSON structure example (UsersData/alex_domains.json):
    {
      "username": "alex",
      "last_full_check": "2025-09-15T14:10:43.201Z",
      "domains": [
        {
          "host": "example.com",
          "added_at": "2025-09-15T12:34:56.000Z",
          "last_check": "2025-09-15T14:10:40.000Z",
          "http": { "ok": true, "status_code": 200, "final_url": "https://example.com/", "error": null },
          "ssl":  { "ok": true, "valid": true, "expires_at": "...", "days_left": 90, "issuer": "..." }
        }
      ]
    }
    """

    # ---------------------------
    # Domain validation
    # ---------------------------

    _FQDN_RE = re.compile(
        r"^(?=.{1,253}$)(?!-)([A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$"
    )

    @staticmethod
    def _normalize_domain(raw: str) -> str:
        """
        Strip scheme, path and port, return lower-case host.
        Examples:
          'HTTPS://Sub.Example.com:443/path' -> 'sub.example.com'
        """
        raw = (raw or "").strip()
        if not raw:
            return ""
        raw = re.sub(r"^https?://", "", raw, flags=re.I)
        host = raw.split("/")[0].split(":")[0]
        return host.lower()

    @classmethod
    def validate_domain(cls, raw_domain: str) -> Tuple[bool, str | None, str | None]:
        """
        Validate and normalize a domain string.
        Returns: (ok, normalized_domain_or_None, reason_if_invalid)
        Reasons: "empty", "format"
        """
        host = cls._normalize_domain(raw_domain)
        if not host:
            return False, None, "empty"
        if not cls._FQDN_RE.match(host):
            return False, None, "format"
        return True, host, None

    # ---------------------------
    # Load / Save
    # ---------------------------

    @staticmethod
    def _empty_user_doc(username: str) -> Dict[str, Any]:
        """Create a fresh user document."""
        return {"username": username, "domains": []}

    def load_user_domains(self, username: str) -> Dict[str, Any]:
        """
        Load (or initialize) the user's domain JSON.
        Always returns a dict with keys: username, domains[, last_full_check].
        """
        path = _domains_path(username)
        with _lock:
            if not os.path.exists(path):
                # Initialize directory and empty file on first access
                os.makedirs(USERS_DATA_DIR, exist_ok=True)
                doc = self._empty_user_doc(username)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(doc, f, ensure_ascii=False, indent=2)
                return doc

            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    # Corrupted file fallback
                    data = self._empty_user_doc(username)

            # Ensure minimal structure
            data.setdefault("username", username)
            data.setdefault("domains", [])
            return data

    def save_user_domains(self, username: str, data: Dict[str, Any]) -> None:
        """
        Persist the user's domain JSON (overwrites the file).
        """
        os.makedirs(USERS_DATA_DIR, exist_ok=True)
        data.setdefault("username", username)
        data.setdefault("domains", [])
        path = _domains_path(username)
        with _lock:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------------------------
    # Mutations (add / remove)
    # ---------------------------

    def add_domain(self, username: str, host: str) -> bool:
        """
        Add a domain if it doesn't exist yet.
        Returns True if added, False if duplicate.
        """
        # Expect a *normalized* host here (validate beforehand)
        host = self._normalize_domain(host)
        if not host:
            return False

        with _lock:
            data = self.load_user_domains(username)
            existing = {d.get("host") for d in data["domains"]}
            if host in existing:
                return False

            data["domains"].append(
                {
                    "host": host,
                    "added_at": _now_iso(),
                    # Optional fields filled later by monitoring:
                    # "last_check": "...",
                    # "http": {...},
                    # "ssl": {...}
                }
            )
            self.save_user_domains(username, data)
            return True

    def remove_domains(self, username: str, hosts: List[str]) -> Dict[str, Any]:
        """
        Remove multiple domains at once.
        Returns dict: {"removed": [...], "not_found": [...]}
        """
        to_remove = {
            self._normalize_domain(h) for h in (hosts or []) if h and h.strip()
        }
        to_remove.discard("")  # remove empties if any

        removed, not_found = [], []

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

            # Any requested domains not present in the current set go to not_found
            for h in to_remove:
                if h not in current:
                    not_found.append(h)

            data["domains"] = new_list
            self.save_user_domains(username, data)

        return {"removed": removed, "not_found": not_found}
