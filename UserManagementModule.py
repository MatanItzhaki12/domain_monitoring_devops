from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, Tuple, Any

# Thread lock for safe file IO
_lock = RLock()

# Directory where user JSON files are stored
USERS_DATA_DIR = os.path.join(os.path.dirname(__file__), "userdata")


def _now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _safe_username(username: str) -> str:
    """Sanitize username for file system usage."""
    return "".join(c for c in (username or "") if c.isalnum() or c in ("-", "_"))


def _domains_path(username: str) -> str:
    """Path to the user's domains file."""
    safe = _safe_username(username)
    return os.path.join(USERS_DATA_DIR, f"{safe}_domains.json")


class UserManager:
    """
    Handles users and per-user domain storage in JSON files.
    """

    # ---------------------------
    # User login / register
    # ---------------------------

    def _users_file(self) -> str:
        return os.path.join(USERS_DATA_DIR, "users.json")

    def validate_login(self, username: str, password: str) -> bool:
        """Return True if username/password pair is valid."""
        path = self._users_file()
        if not os.path.exists(path):
            return False
        with open(path, "r", encoding="utf-8") as f:
            try:
                users = json.load(f)
            except json.JSONDecodeError:
                return False
        return username in users and users[username] == password

    def register_user(self, username: str, password: str) -> bool:
        """Register a new user. Returns False if user already exists."""
        os.makedirs(USERS_DATA_DIR, exist_ok=True)
        path = self._users_file()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    users = json.load(f)
                except json.JSONDecodeError:
                    users = {}
        else:
            users = {}

        if username in users:
            return False

        users[username] = password
        with open(path, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True

    # ---------------------------
    # Domain validation
    # ---------------------------

    _FQDN_RE = re.compile(
        r"^(?=.{1,253}$)(?!-)([A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$"
    )

    @staticmethod
    def _normalize_domain(raw: str) -> str:
        raw = (raw or "").strip()
        if not raw:
            return ""
        raw = re.sub(r"^https?://", "", raw, flags=re.I)
        host = raw.split("/")[0].split(":")[0]
        return host.lower()

    @classmethod
    def validate_domain(cls, raw_domain: str) -> Tuple[bool, str | None, str | None]:
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
        return {"username": username, "domains": []}

    def load_user_domains(self, username: str) -> Dict[str, Any]:
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
        os.makedirs(USERS_DATA_DIR, exist_ok=True)
        path = _domains_path(username)
        with _lock:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------------------------
    # Add / Remove domains
    # ---------------------------

    def add_domain(self, username: str, host: str) -> bool:
        host = self._normalize_domain(host)
        if not host:
            return False
        with _lock:
            data = self.load_user_domains(username)
            existing = {d.get("host") for d in data["domains"]}
            if host in existing:
                return False
            data["domains"].append({"host": host, "added_at": _now_iso()})
            self.save_user_domains(username, data)
            return True

    def remove_domains(self, username: str, hosts: List[str]) -> Dict[str, Any]:
        to_remove = {
            self._normalize_domain(h) for h in (hosts or []) if h and h.strip()
        }
        to_remove.discard("")
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
            for h in to_remove:
                if h not in current:
                    not_found.append(h)
            data["domains"] = new_list
            self.save_user_domains(username, data)
        return {"removed": removed, "not_found": not_found}
