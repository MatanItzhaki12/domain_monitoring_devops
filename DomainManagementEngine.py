# DomainManagementEngine.py
from __future__ import annotations

import os
import re
from time import time
from typing import Dict, List, Tuple, Any, Optional
from threading import RLock

# Optional: faster JSON with fallback to stdlib json
try:
    import orjson as _fastjson  # pip install orjson
    def _jloads(b: bytes):
        return _fastjson.loads(b)
    def _jdumps(o: Any) -> bytes:
        # orjson returns bytes; option to pretty-print if needed:
        return _fastjson.dumps(o, option=_fastjson.OPT_INDENT_2 | _fastjson.OPT_NON_STR_KEYS)
except Exception:
    import json as _fastjson
    def _jloads(b: bytes):
        # stdlib json loads from str -> decode
        return _fastjson.loads(b.decode("utf-8"))
    def _jdumps(o: Any) -> bytes:
        return _fastjson.dumps(o, ensure_ascii=False, indent=2).encode("utf-8")

from logger import setup_logger
logger = setup_logger("DomainManagementEngine")

# ----------------------------
# Thread-safety for file IO
# ----------------------------
_lock = RLock()

# ----------------------------
# Base directory for per-user JSON files
# ----------------------------
BASE_DIR = os.path.dirname(__file__)
USERS_DATA_DIR = os.path.join(BASE_DIR, "UsersData")


def _domains_path(username: str) -> str:
    """Generate per-user JSON file path <username>_domains.json."""
    safe_user = re.sub(r"[^A-Za-z0-9_.-]", "_", (username or "").strip())
    return os.path.join(USERS_DATA_DIR, f"{safe_user}_domains.json")


class DomainManagementEngine:
    """
    File-backed user domain storage and domain validation/CRUD.

    Per-user file format (JSON List):
    [
      {
        "domain": "example.com",
        "status": "Pending" | "Live" | "Down",
        "ssl_expiration": "YYYY-MM-DD" | "N/A",
        "ssl_issuer": "CA name" | "N/A"
      }
    ]
    """

    # Regex for FQDN validation (example.com, sub.example.co.il, etc.)
    _FQDN_RE = re.compile(
        r"^(?=.{1,253}$)(?!-)([A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$"
    )

    def __init__(self, user_manager: Optional[object] = None):
        """
        :param user_manager: Optional UserManager for future integrations.
        """
        self.user_manager = user_manager
        os.makedirs(USERS_DATA_DIR, exist_ok=True)

        # In-memory read-through/write-through cache:
        # { username: {"data": list[dict], "mtime": float, "last": float, "index": dict[str,int]} }
        self._cache: Dict[str, Dict[str, Any]] = {}

    # ----------------------------
    # Helpers: normalization & validation
    # ----------------------------
    @staticmethod
    def _normalize_domain(raw: str) -> str:
        """Normalize domain: strip scheme/port/paths, lowercase, remove trailing dot."""
        if not raw:
            return ""
        s = raw.strip().lower()

        if s.startswith("http://"):
            s = s[7:]
        elif s.startswith("https://"):
            s = s[8:]

        # Cut path, query, fragment
        s = s.split("/", 1)[0]
        s = s.split("?", 1)[0]
        s = s.split("#", 1)[0]

        # Remove port
        if ":" in s:
            s = s.split(":", 1)[0]

        # Remove trailing dot
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

    # ----------------------------
    # Helpers: file IO with caching
    # ----------------------------
    def _ensure_user_file(self, username: str) -> None:
        """Ensure per-user domain file exists and is a JSON list."""
        path = _domains_path(username)
        if not os.path.exists(path):
            os.makedirs(USERS_DATA_DIR, exist_ok=True)
            # Write empty list atomically
            tmp = f"{path}.tmp"
            with open(tmp, "wb") as f:
                f.write(_jdumps([]))
            os.replace(tmp, path)

    @staticmethod
    def _build_index(data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Create a domain -> index mapping."""
        idx: Dict[str, int] = {}
        for i, row in enumerate(data):
            d = row.get("domain")
            if isinstance(d, str):
                idx[d] = i
        return idx

    def _read_fast(self, username: str) -> List[Dict[str, Any]]:
        """
        Read-through cache:
        - If file mtime unchanged, return cached list
        - Else, read from disk, update cache
        """
        path = _domains_path(username)
        self._ensure_user_file(username)

        try:
            mtime = os.path.getmtime(path)
        except FileNotFoundError:
            # File could be created concurrently; ensure and retry
            self._ensure_user_file(username)
            mtime = os.path.getmtime(path)

        c = self._cache.get(username)
        if c and c.get("mtime") == mtime:
            return c["data"]

        # Load from disk
        try:
            with open(path, "rb") as f:
                data = _jloads(f.read())
            if not isinstance(data, list):
                data = []
        except Exception as e:
            logger.warning(f"Failed to read domains file for {username}: {e}")
            data = []

        self._cache[username] = {
            "data": data,
            "mtime": mtime,
            "last": time(),
            "index": self._build_index(data),
        }
        return data

    def _write_fast(self, username: str, data: List[Dict[str, Any]]) -> None:
        """
        Write-through cache:
        - Single atomic write (.tmp + os.replace)
        - Update cache and mtime
        """
        path = _domains_path(username)
        tmp = f"{path}.tmp"

        try:
            payload = _jdumps(data)
            with open(tmp, "wb") as f:
                f.write(payload)
            os.replace(tmp, path)
            mtime = os.path.getmtime(path)

            self._cache[username] = {
                "data": data,
                "mtime": mtime,
                "last": time(),
                "index": self._build_index(data),
            }
        finally:
            # Best effort cleanup in rare failure scenarios
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass

    # ----------------------------
    # Public API
    # ----------------------------
    def list_domains(self, username: str) -> List[Dict[str, Any]]:
        """Return all domain entries for user (cached)."""
        with _lock:
            return list(self._read_fast(username))  # return a shallow copy

    def add_domain(self, username: str, raw_domain: str) -> Tuple[bool, Optional[str]]:
        """
        Validate and add a single domain.
        Returns (added_ok, error_code|None) where error_code in {"invalid","duplicate"}.
        """
        ok, host, _reason = self.validate_domain(raw_domain)
        if not ok or not host:
            return False, "invalid"
        return self.add_domain_trusted(username, host)

    def add_domain_trusted(self, username: str, normalized_host: str) -> Tuple[bool, Optional[str]]:
        """
        Add a domain assuming it is already normalized and valid.
        Returns (added_ok, error_code|None) where error_code in {"duplicate"}.
        """
        with _lock:
            data = self._read_fast(username)
            idx = self._cache[username]["index"]  # updated by _read_fast
            if normalized_host in idx:
                return False, "duplicate"

            data.append({
                "domain": normalized_host,
                "status": "Pending",
                "ssl_expiration": "N/A",
                "ssl_issuer": "N/A",
            })
            # Update cache index incrementally before write (optional)
            idx[normalized_host] = len(data) - 1
            self._write_fast(username, data)
            return True, None

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
        if not os.path.exists(file_path):
            logger.error(f"Bulk upload failed: file not found -> {file_path}")
            return {"ok": False, "error": "File not found"}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.exception(f"Failed to read bulk upload file: {e}")
            return {"ok": False, "error": "Could not read file"}

        if not raw_lines:
            return {"ok": False, "error": "File is empty or invalid"}

        added: List[str] = []
        duplicates: List[str] = []
        invalid: List[Dict[str, str]] = []

        with _lock:
            data = self._read_fast(username)
            idx = self._cache[username]["index"]

            # Validate & stage additions without writing on each step
            staged: List[Dict[str, Any]] = []

            for raw in raw_lines:
                ok, normalized, reason = self.validate_domain(raw)
                if not ok or not normalized:
                    invalid.append({"input": raw, "reason": reason or "invalid"})
                    continue
                if normalized in idx:
                    duplicates.append(normalized)
                    continue
                staged.append({
                    "domain": normalized,
                    "status": "Pending",
                    "ssl_expiration": "N/A",
                    "ssl_issuer": "N/A",
                })
                added.append(normalized)
                # Optimistically update in-memory index to prevent double adds in same batch
                idx[normalized] = len(data) + len(staged) - 1

            if staged:
                data.extend(staged)
                self._write_fast(username, data)
            # If nothing staged, cache/FS remain intact

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
        :param hosts: list of domain strings (raw or normalized)
        :return: {"removed": [.], "not_found": [.]}
        """
        to_remove = set()
        for h in hosts or []:
            if not h:
                continue
            norm = self._normalize_domain(h)
            if norm:
                to_remove.add(norm)

        with _lock:
            data = self._read_fast(username)
            idx = self._cache[username]["index"]

            removed = []
            # Build a set for fast lookup
            current_set = set(idx.keys())
            targets = list(to_remove)

            # Fast path: if none exist, short-circuit
            any_exist = any(t in current_set for t in targets)
            if not any_exist:
                return {"removed": [], "not_found": sorted(list(to_remove))}

            # Filter out rows to keep
            new_list = [row for row in data if row.get("domain") not in to_remove]
            removed = sorted(list(current_set.intersection(to_remove)))
            not_found = sorted(list(to_remove - current_set))

            self._write_fast(username, new_list)  # also rebuilds index
            return {"removed": removed, "not_found": not_found}

    def update_fields(self, username: str, updates: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch update specific fields for multiple domains.
        Example:
            updates = {
              "example.com": {"status": "Live", "ssl_expiration": "2026-01-01", "ssl_issuer": "LE"},
              "foo.bar": {"status": "Down"}
            }
        Returns: {"ok": True, "updated": ["example.com", ...], "skipped": ["missing.com", ...]}
        """
        if not isinstance(updates, dict) or not updates:
            return {"ok": False, "error": "updates must be a non-empty dict"}

        updated: List[str] = []
        skipped: List[str] = []

        with _lock:
            data = self._read_fast(username)
            idx = self._cache[username]["index"]
            changed = False

            for host, fields in updates.items():
                if not isinstance(fields, dict):
                    continue
                norm = self._normalize_domain(host)
                if not norm or norm not in idx:
                    skipped.append(host)
                    continue

                row = data[idx[norm]]
                applied = False
                for k, v in fields.items():
                    if row.get(k) != v:
                        row[k] = v
                        applied = True
                        changed = True
                if applied:
                    updated.append(norm)

            if changed:
                self._write_fast(username, data)

        return {"ok": True, "updated": updated, "skipped": skipped}

    # ----------------------------
    # Compatibility helper
    # ----------------------------
    def load_user_domains(self, username: str) -> List[Dict[str, Any]]:
        """
        Ensure user file exists and return current list.
        This keeps compatibility with code that calls dme.load_user_domains(username).
        """
        with _lock:
            return self._read_fast(username)

    # ----------------------------
    # Optional utility
    # ----------------------------
    def clear_cache(self, username: Optional[str] = None) -> None:
        """Clear in-memory cache for a specific user or all users."""
        with _lock:
            if username is None:
                self._cache.clear()
            else:
                self._cache.pop(username, None)
