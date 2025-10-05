# client_base/models/DomainManagementEngine.py
# -*- coding: utf-8 -*-
"""
DomainManagementEngine

Purpose:
- Provide domain normalization & validation
- Provide CRUD operations for a user's domains file
- Persist data strictly in the LLD format

Per LLD, each user's file (<username>_domains.json) MUST be a JSON ARRAY:
[
  {
    "domain": "example.com",
    "status": "Pending",
    "ssl_expiration": "N/A",
    "ssl_issuer": "N/A"
  }
]

"""

from __future__ import annotations

import json
import os
import re
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

# ----------------------------
# Base directory for per-user JSON files
# ----------------------------
BASE_DIR = os.path.dirname(__file__)
USERDATA_DIR = os.path.join(BASE_DIR, "userdata")

# Thread-safety for file IO
_LOCK = RLock()

# Strict yet practical FQDN regex:
# - label: 1..63 chars, starts/ends with alnum, may contain hyphens
# - total length <= 253
# - TLD: 2..63 letters
_FQDN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$",
    re.IGNORECASE,
)


# ---------- Path helpers ----------

def _ensure_userdata_dir() -> None:
    """Make sure the userdata directory exists."""
    if not os.path.isdir(USERDATA_DIR):
        os.makedirs(USERDATA_DIR, exist_ok=True)


def _domains_path(username: str) -> str:
    """Return full path for <username>_domains.json (sanitized name)."""
    safe_user = re.sub(r"[^A-Za-z0-9_.-]", "_", (username or "").strip())
    return os.path.join(USERDATA_DIR, f"{safe_user}_domains.json")


# ---------- Normalization & validation ----------

def _normalize_domain(raw: str) -> str:
    """
    Normalize a domain string:
    - strip scheme (http/https)
    - strip leading 'www.'
    - drop path/query/fragment
    - drop :port
    - lower-case
    - drop trailing dot
    """
    if not raw:
        return ""
    s = raw.strip().lower()

    # strip scheme
    if s.startswith("http://"):
        s = s[7:]
    elif s.startswith("https://"):
        s = s[8:]

    # strip leading www.
    if s.startswith("www."):
        s = s[4:]

    # drop path/query/fragment
    s = s.split("/", 1)[0]
    s = s.split("?", 1)[0]
    s = s.split("#", 1)[0]

    # drop port
    if ":" in s:
        s = s.split(":", 1)[0]

    # drop trailing dot
    if s.endswith("."):
        s = s[:-1]

    return s


def validate_domain(raw_domain: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate a single domain against FQDN rules.

    Returns:
        (ok, normalized_domain_or_None, reason_or_None)
    """
    dom = _normalize_domain(raw_domain)
    if not dom:
        return False, None, "Empty domain"

    if not _FQDN_RE.match(dom):
        return False, None, "Domain format is invalid (expected e.g. example.com)"

    return True, dom, None


# ---------- File I/O (LLD array format) ----------

def _load_user_domains(username: str) -> List[Dict[str, Any]]:
    """
    Load the user's domains file. If the file does not exist or malformed,
    return an empty list (LLD array format).
    """
    _ensure_userdata_dir()
    path = _domains_path(username)
    with _LOCK:
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return []
        return data if isinstance(data, list) else []


def _save_user_domains(username: str, domains: List[Dict[str, Any]]) -> None:
    """
    Save the user's domains to disk as a JSON ARRAY (LLD format).
    This function is atomic at the file level (write to temp then replace).
    """
    _ensure_userdata_dir()
    path = _domains_path(username)
    tmp = f"{path}.tmp"
    with _LOCK:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(domains, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)


# ---------- Public API (used by routes/services) ----------

def list_domains(username: str) -> List[Dict[str, Any]]:
    """
    Return the user's domain list (LLD array).
    Useful for dashboard rendering.
    """
    return _load_user_domains(username)


def add_domain(username: str, raw_domain: str) -> Tuple[bool, str]:
    """
    Add a single domain to <username>_domains.json.

    Behavior:
    - Validate domain format
    - Deduplicate (no-op if already present)
    - Initialize LLD fields:
        status="Pending", ssl_expiration="N/A", ssl_issuer="N/A"

    Returns:
        (ok, message)
    """
    ok, dom, reason = validate_domain(raw_domain)
    if not ok or not dom:
        return False, f"Invalid domain: {reason}"

    with _LOCK:
        domains = _load_user_domains(username)
        if any(d.get("domain") == dom for d in domains):
            return False, "Domain already exists"

        domains.append(
            {
                "domain": dom,
                "status": "Pending",
                "ssl_expiration": "N/A",
                "ssl_issuer": "N/A",
            }
        )
        _save_user_domains(username, domains)
        return True, "Domain added successfully"


def remove_domains(username: str, raw_domains: List[str]) -> Dict[str, List[str]]:
    """
    Remove one or more domains from <username>_domains.json.

    Args:
        raw_domains: list of raw domain strings (may include schemes/ports)

    Returns:
        {
          "removed":   [<domain>, ...],
          "not_found": [<domain>, ...]
        }
    """
    targets = { _normalize_domain(x) for x in (raw_domains or []) if (x or "").strip() }
    targets.discard("")

    removed: List[str] = []
    not_found: List[str] = []

    with _LOCK:
        domains = _load_user_domains(username)
        existing_set = { d.get("domain") for d in domains }

        # Compute results
        removed = sorted(list(existing_set & targets))
        not_found = sorted(list(targets - existing_set))

        # Filter out removed ones
        new_list = [d for d in domains if d.get("domain") not in targets]
        _save_user_domains(username, new_list)

    return {"removed": removed, "not_found": not_found}


# --------- Optional helpers for bulk workflows (routes handle file IO) ---------

def validate_domains_batch(candidates: List[str]) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Validate multiple domains (used by /bulk_upload route after reading .txt).

    Returns:
        (valid_domains, invalid_pairs)
        invalid_pairs is a list of (raw_input, reason)
    """
    valid: List[str] = []
    invalid: List[Tuple[str, str]] = []

    for raw in candidates or []:
        ok, dom, reason = validate_domain(raw)
        if ok and dom:
            valid.append(dom)
        else:
            invalid.append((raw, reason or "Invalid"))

    return valid, invalid


def add_domains_batch(username: str, domains: List[str]) -> Dict[str, Any]:
    """
    Add multiple validated domains at once.
    Expects all inputs to be normalized/validated already.

    Returns:
        {
          "added": <int>,
          "duplicates": <int>
        }
    """
    added = 0
    dups = 0

    with _LOCK:
        current = _load_user_domains(username)
        existing = {d.get("domain") for d in current}

        for dom in domains or []:
            if dom in existing:
                dups += 1
                continue
            current.append({
                "domain": dom,
                "status": "Pending",
                "ssl_expiration": "N/A",
                "ssl_issuer": "N/A"
            })
            existing.add(dom)
            added += 1

        _save_user_domains(username, current)

    return {"added": added, "duplicates": dups}
