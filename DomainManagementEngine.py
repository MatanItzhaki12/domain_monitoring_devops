# DomainManagementEngine.py
from __future__ import annotations

import os, re, hashlib
from time import time
from typing import Dict, List, Tuple, Any, Optional
from threading import RLock

from logger import setup_logger
log = setup_logger("DomainManagementEngine")

# ----------------------------
# Switches (choose storage style)
# ----------------------------
# "per_user"   -> старое поведение: 1 файл на пользователя (можно ещё и зашардить по подпапкам)
# "single"     -> один общий файл UsersData/domains_store.json с ключами = username
STORAGE_MODE = os.environ.get("DME_STORAGE_MODE", "single").lower()  # "single" по умолчанию
SHARD_LEN = 2  # для per_user+шардинг: длина префикса подпапки

# ----------------------------
# JSON backend (быстрый -> orjson)
# ----------------------------
try:
    import orjson as _json
    def _jloads(b: bytes): return _json.loads(b)
    def _jdumps(o: Any) -> bytes:
        return _json.dumps(o, option=_json.OPT_INDENT_2 | _json.OPT_NON_STR_KEYS)
except Exception:
    import json as _json
    def _jloads(b: bytes): return _json.loads(b.decode("utf-8"))
    def _jdumps(o: Any) -> bytes: return _json.dumps(o, ensure_ascii=False, indent=2).encode("utf-8")

# ----------------------------
# Paths & locks
# ----------------------------
_lock = RLock()
BASE_DIR = os.path.dirname(__file__)
USERS_DATA_DIR = os.path.join(BASE_DIR, "UsersData")
STORE_FILE = os.path.join(USERS_DATA_DIR, "domains_store.json")  # single-file mode

def _safe_user(username: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", (username or "").strip())

def _user_shard(username: str) -> str:
    h = hashlib.sha1(username.encode("utf-8")).hexdigest()
    return h[:SHARD_LEN] if SHARD_LEN > 0 else ""

def _domains_path(username: str) -> str:
    """Per-user json path (with sharding)."""
    u = _safe_user(username)
    shard = _user_shard(u)
    if shard:
        p = os.path.join(USERS_DATA_DIR, shard)
        os.makedirs(p, exist_ok=True)
        return os.path.join(p, f"{u}_domains.json")
    else:
        return os.path.join(USERS_DATA_DIR, f"{u}_domains.json")

# ----------------------------
# Engine
# ----------------------------
class DomainManagementEngine:
    """
    File-backed storage for domains with caching and atomic writes.
    Compatible public API:
      - list_domains(username)
      - add_domain / add_domain_trusted
      - bulk_upload(username, file_path)
      - remove_domains(username, hosts)
      - update_fields(username, updates)
      - load_user_domains(username)
    """

    _FQDN_RE = re.compile(r"^(?=.{1,253}$)(?!-)([A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$")

    def __init__(self, user_manager: Optional[object] = None):
        self.user_manager = user_manager
        os.makedirs(USERS_DATA_DIR, exist_ok=True)
        # cache shapes:
        # per_user mode:    {username: {"data": list, "mtime": float, "index": {domain:i}, "last": ts}}
        # single-file mode: {"__STORE__": {"data": dict[user->list], "mtime": float, "last": ts},
        #                    username:    {"index": {domain:i}}}
        self._cache: Dict[str, Dict[str, Any]] = {}

    # ---------- normalization & validation ----------
    @staticmethod
    def _normalize_domain(raw: str) -> str:
        if not raw:
            return ""
        s = raw.strip().lower()
        if s.startswith("http://"):  s = s[7:]
        elif s.startswith("https://"): s = s[8:]
        s = s.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
        if ":" in s: s = s.split(":", 1)[0]
        if s.endswith("."): s = s[:-1]
        return s

    def validate_domain(self, raw_domain: str) -> Tuple[bool, Optional[str], Optional[str]]:
        host = self._normalize_domain(raw_domain)
        if not host:
            return False, None, "Empty domain"
        if not self._FQDN_RE.match(host):
            return False, None, "Domain does not match FQDN format"
        return True, host, None

    # ---------- low-level IO with caching ----------
    @staticmethod
    def _build_index(data: List[Dict[str, Any]]) -> Dict[str, int]:
        idx = {}
        for i, row in enumerate(data):
            d = row.get("domain")
            if isinstance(d, str):
                idx[d] = i
        return idx

    # ----- per-user files -----
    def _ensure_user_file(self, username: str) -> str:
        path = _domains_path(username)
        if not os.path.exists(path):
            tmp = f"{path}.tmp"
            with open(tmp, "wb") as f:
                f.write(_jdumps([]))
            os.replace(tmp, path)
        return path

    def _read_user_fast(self, username: str) -> List[Dict[str, Any]]:
        path = self._ensure_user_file(username)
        mtime = os.path.getmtime(path)
        c = self._cache.get(username)
        if c and c.get("mtime") == mtime:
            return c["data"]
        try:
            with open(path, "rb") as f:
                data = _jloads(f.read())
            if not isinstance(data, list):
                data = []
        except Exception:
            data = []
        self._cache[username] = {
            "data": data, "mtime": mtime, "last": time(), "index": self._build_index(data)
        }
        return data

    def _write_user_fast(self, username: str, data: List[Dict[str, Any]]) -> None:
        path = self._ensure_user_file(username)
        tmp = f"{path}.tmp"
        with open(tmp, "wb") as f:
            f.write(_jdumps(data))
        os.replace(tmp, path)
        mtime = os.path.getmtime(path)
        self._cache[username] = {
            "data": data, "mtime": mtime, "last": time(), "index": self._build_index(data)
        }

    # ----- single-file store -----
    def _ensure_store(self) -> None:
        if not os.path.exists(STORE_FILE):
            tmp = f"{STORE_FILE}.tmp"
            with open(tmp, "wb") as f:
                f.write(_jdumps({}))
            os.replace(tmp, STORE_FILE)

    def _read_store(self) -> Dict[str, List[Dict[str, Any]]]:
        self._ensure_store()
        mtime = os.path.getmtime(STORE_FILE)
        c = self._cache.get("__STORE__")
        if c and c.get("mtime") == mtime:
            return c["data"]
        try:
            with open(STORE_FILE, "rb") as f:
                data = _jloads(f.read())
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
        self._cache["__STORE__"] = {"data": data, "mtime": mtime, "last": time()}
        # build per-user indexes
        for u, arr in data.items():
            self._cache[u] = {"index": self._build_index(arr)}
        return data

    def _write_store(self, store: Dict[str, List[Dict[str, Any]]]) -> None:
        tmp = f"{STORE_FILE}.tmp"
        with open(tmp, "wb") as f:
            f.write(_jdumps(store))
        os.replace(tmp, STORE_FILE)
        mtime = os.path.getmtime(STORE_FILE)
        self._cache["__STORE__"] = {"data": store, "mtime": mtime, "last": time()}
        # rebuild per-user indexes
        for u, arr in store.items():
            self._cache[u] = {"index": self._build_index(arr)}

    # ---------- public API ----------
    def list_domains(self, username: str) -> List[Dict[str, Any]]:
        with _lock:
            if STORAGE_MODE == "single":
                store = self._read_store()
                arr = store.get(username) or []
                # лёгкая копия
                return list(arr)
            else:
                return list(self._read_user_fast(username))

    def add_domain(self, username: str, raw_domain: str) -> Tuple[bool, Optional[str]]:
        ok, host, _ = self.validate_domain(raw_domain)
        if not ok or not host:
            return False, "invalid"
        return self.add_domain_trusted(username, host)

    def add_domain_trusted(self, username: str, normalized_host: str) -> Tuple[bool, Optional[str]]:
        with _lock:
            if STORAGE_MODE == "single":
                store = self._read_store()
                arr = store.setdefault(username, [])
                idx = self._cache.get(username, {}).get("index") or self._build_index(arr)
                if normalized_host in idx:
                    return False, "duplicate"
                arr.append({"domain": normalized_host, "status": "Pending", "ssl_expiration": "N/A", "ssl_issuer": "N/A"})
                self._write_store(store)
                return True, None
            else:
                data = self._read_user_fast(username)
                idx = self._cache[username]["index"]
                if normalized_host in idx:
                    return False, "duplicate"
                data.append({"domain": normalized_host, "status": "Pending", "ssl_expiration": "N/A", "ssl_issuer": "N/A"})
                self._write_user_fast(username, data)
                return True, None

    def bulk_upload(self, username: str, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            log.error(f"Bulk upload failed: file not found -> {file_path}")
            return {"ok": False, "error": "File not found"}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            log.exception(f"Failed to read bulk upload file: {e}")
            return {"ok": False, "error": "Could not read file"}
        if not raw_lines:
            return {"ok": False, "error": "File is empty or invalid"}

        added, duplicates, invalid = [], [], []
        with _lock:
            if STORAGE_MODE == "single":
                store = self._read_store()
                arr = store.setdefault(username, [])
                idx = self._cache.get(username, {}).get("index") or self._build_index(arr)
                staged = []
                for raw in raw_lines:
                    ok, norm, reason = self.validate_domain(raw)
                    if not ok or not norm:
                        invalid.append({"input": raw, "reason": reason or "invalid"})
                        continue
                    if norm in idx:
                        duplicates.append(norm)
                        continue
                    staged.append({"domain": norm, "status": "Pending", "ssl_expiration": "N/A", "ssl_issuer": "N/A"})
                    added.append(norm)
                    idx[norm] = len(arr) + len(staged) - 1
                if staged:
                    arr.extend(staged)
                    self._write_store(store)
            else:
                data = self._read_user_fast(username)
                idx = self._cache[username]["index"]
                staged = []
                for raw in raw_lines:
                    ok, norm, reason = self.validate_domain(raw)
                    if not ok or not norm:
                        invalid.append({"input": raw, "reason": reason or "invalid"})
                        continue
                    if norm in idx:
                        duplicates.append(norm)
                        continue
                    staged.append({"domain": norm, "status": "Pending", "ssl_expiration": "N/A", "ssl_issuer": "N/A"})
                    added.append(norm)
                    idx[norm] = len(data) + len(staged) - 1
                if staged:
                    data.extend(staged)
                    self._write_user_fast(username, data)

        return {"ok": True, "summary": {"added": added, "duplicates": duplicates, "invalid": invalid}}

    def remove_domains(self, username: str, hosts: List[str]) -> Dict[str, List[str]]:
        to_remove = set()
        for h in hosts or []:
            if not h: continue
            n = self._normalize_domain(h)
            if n: to_remove.add(n)

        with _lock:
            if STORAGE_MODE == "single":
                store = self._read_store()
                arr = store.get(username) or []
                idx = self._cache.get(username, {}).get("index") or self._build_index(arr)
                current = set(idx.keys())
                new_arr = [row for row in arr if row.get("domain") not in to_remove]
                removed = sorted(list(current.intersection(to_remove)))
                not_found = sorted(list(to_remove - current))
                store[username] = new_arr
                self._write_store(store)
                return {"removed": removed, "not_found": not_found}
            else:
                data = self._read_user_fast(username)
                idx = self._cache[username]["index"]
                current = set(idx.keys())
                new_list = [row for row in data if row.get("domain") not in to_remove]
                removed = sorted(list(current.intersection(to_remove)))
                not_found = sorted(list(to_remove - current))
                self._write_user_fast(username, new_list)
                return {"removed": removed, "not_found": not_found}

    def update_fields(self, username: str, updates: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(updates, dict) or not updates:
            return {"ok": False, "error": "updates must be a non-empty dict"}
        updated, skipped = [], []

        with _lock:
            if STORAGE_MODE == "single":
                store = self._read_store()
                arr = store.setdefault(username, [])
                idx = self._cache.get(username, {}).get("index") or self._build_index(arr)
                changed = False
                for host, fields in updates.items():
                    norm = self._normalize_domain(host)
                    if not norm or norm not in idx:
                        skipped.append(host); continue
                    row = arr[idx[norm]]
                    applied = False
                    for k, v in fields.items():
                        if row.get(k) != v:
                            row[k] = v; applied = True; changed = True
                    if applied: updated.append(norm)
                if changed: self._write_store(store)
            else:
                data = self._read_user_fast(username)
                idx = self._cache[username]["index"]
                changed = False
                for host, fields in updates.items():
                    norm = self._normalize_domain(host)
                    if not norm or norm not in idx:
                        skipped.append(host); continue
                    row = data[idx[norm]]
                    applied = False
                    for k, v in fields.items():
                        if row.get(k) != v:
                            row[k] = v; applied = True; changed = True
                    if applied: updated.append(norm)
                if changed: self._write_user_fast(username, data)

        return {"ok": True, "updated": updated, "skipped": skipped}


    def load_user_domains(self, username: str) -> List[Dict[str, Any]]:
        with _lock:
            return self.list_domains(username)
