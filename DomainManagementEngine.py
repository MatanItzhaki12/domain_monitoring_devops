<<<<<<< HEAD
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, Tuple, Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from logger import setup_logger

# ----------------------------
# Thread-safety for DB IO
# ----------------------------
_lock = RLock()


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 with 'Z' suffix."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _utc_now_dt() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class DomainManagementEngine:
    """
    Postgres-backed user domain storage and domain validation/CRUD.
    """

    # Regex for FQDN validation (example.com, sub.example.co.il etc.)
    _FQDN_RE = re.compile(
        r"^(?=.{1,253}$)(?!-)([A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$"
    )

    def __init__(self, db_url: Optional[str] = None):
        self.logger = setup_logger("DomainManagementEngine")
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise RuntimeError("DATABASE_URL is not set (postgresql://user:pass@host:5432/dbname)")

    def _conn(self):
        return psycopg2.connect(self.db_url)

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

    # ---------------------------------------------------------------------
    # DB methods (replace file-based load/save)
    # ---------------------------------------------------------------------

    def load_user_domains(self, username: str) -> List[Dict[str, Any]]:
        """
        Pull user's domains from Postgres for dashboard.
        """
        sql = """
            SELECT
              domain,
              status,
              ssl_expiration,
              ssl_issuer,
              added_at,
              last_check
            FROM public.user_domains
            WHERE username = %s
            ORDER BY lower(domain) ASC;
        """
        with _lock:
            with self._conn() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(sql, (username,))
                    return [dict(r) for r in (cur.fetchall() or [])]

    def save_user_domains(self, username: str, data: List[Dict[str, Any]]) -> None:
        """
        No-op in Postgres mode. Persistence is done via INSERT/DELETE/UPDATE queries.
        """
        return

    def list_domains(self, username: str) -> List[Dict[str, Any]]:
        return self.load_user_domains(username)

    def set_last_full_check_now(self, username: str) -> None:
        """Update last full check timestamp (to be called after MonitoringSystem run)."""
        sql = """
            INSERT INTO public.user_domain_meta (username, last_full_check)
            VALUES (%s, %s)
            ON CONFLICT (username)
            DO UPDATE SET last_full_check = EXCLUDED.last_full_check;
        """
        with _lock:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (username, _utc_now_dt()))
                conn.commit()

    def add_domain(self, username: str, raw_domain: str) -> bool:
        ok, host, _reason = self.validate_domain(raw_domain)
        if not ok or not host:
            return False

        sql = """
            INSERT INTO public.user_domains
            (username, domain, status, ssl_expiration, ssl_issuer, added_at)
            VALUES (%s, %s, 'Pending', 'N/A', 'N/A', now())
            ON CONFLICT (username, domain) DO NOTHING;
        """
        with _lock:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (username, host))
                    inserted = (cur.rowcount == 1)
                conn.commit()
        return inserted

    def bulk_upload(self, username: str, file_path: str) -> Dict[str, Any]:
        """
        Bulk upload domains from a text file.
        Each valid line is inserted into Postgres with ON CONFLICT DO NOTHING.
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

        added: List[str] = []
        duplicates: List[str] = []
        invalid: List[Dict[str, str]] = []

        insert_sql = """
            INSERT INTO public.user_domains
            (username, domain, status, ssl_expiration, ssl_issuer, added_at)
            VALUES (%s, %s, 'Pending', 'N/A', 'N/A', now())
            ON CONFLICT (username, domain) DO NOTHING;
        """

        with _lock:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    for raw in domains_to_add:
                        ok, normalized, reason = self.validate_domain(raw)
                        if not ok or not normalized:
                            logger.warning(f"Invalid domain skipped: {raw} ({reason})")
                            invalid.append({"input": raw, "reason": reason or "Invalid"})
                            continue

                        cur.execute(insert_sql, (username, normalized))
                        if cur.rowcount == 1:
                            added.append(normalized)
                        else:
                            duplicates.append(normalized)

                conn.commit()

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
        Remove domains from the user's list (Postgres).
        :param hosts: list of domain strings
        :return: {"removed": [...], "not_found": [...]}
        """
        to_remove = {self._normalize_domain(h) for h in (hosts or []) if h and h.strip()}
        to_remove.discard("")
        to_remove_list = sorted(to_remove)

        if not to_remove_list:
            return {"removed": [], "not_found": []}

        select_sql = """
            SELECT domain
            FROM public.user_domains
            WHERE username = %s AND domain = ANY(%s);
        """

        delete_sql = """
            DELETE FROM public.user_domains
            WHERE username = %s AND domain = ANY(%s);
        """

        with _lock:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(select_sql, (username, to_remove_list))
                    existing = {row[0] for row in (cur.fetchall() or [])}

                    cur.execute(delete_sql, (username, to_remove_list))
                conn.commit()

        return {
            "removed": sorted(existing),
            "not_found": sorted(set(to_remove_list) - existing)
        }
=======
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, List, Tuple, Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from logger import setup_logger

_lock = RLock()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _utc_now_dt() -> datetime:
    return datetime.now(timezone.utc)


class DomainManagementEngine:
    _FQDN_RE = re.compile(r"^(?=.{1,253}$)(?!-)([A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$")

    def __init__(self, db_url: Optional[str] = None):
        self.logger = setup_logger("DomainManagementEngine")
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise RuntimeError("DATABASE_URL is not set (postgresql://user:pass@host:5432/dbname)")

    def _conn(self):
        return psycopg2.connect(self.db_url)

    @staticmethod
    def _normalize_domain(raw: str) -> str:
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
        host = self._normalize_domain(raw_domain)
        if not host:
            return False, None, "Empty domain"
        if not self._FQDN_RE.match(host):
            return False, None, "Domain does not match FQDN format"
        return True, host, None

    def load_user_domains(self, username: str) -> List[Dict[str, Any]]:
        sql = """
            SELECT
              domain,
              status,
              ssl_expiration,
              ssl_issuer,
              added_at,
              last_check
            FROM public.user_domains
            WHERE username = %s
            ORDER BY lower(domain) ASC;
        """
        with _lock:
            with self._conn() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(sql, (username,))
                    return [dict(r) for r in (cur.fetchall() or [])]

    def save_user_domains(self, username: str, data: List[Dict[str, Any]]) -> None:
        return

    def list_domains(self, username: str) -> List[Dict[str, Any]]:
        return self.load_user_domains(username)

    def set_last_full_check_now(self, username: str) -> None:
        sql = """
            INSERT INTO public.user_domain_meta (username, last_full_check)
            VALUES (%s, %s)
            ON CONFLICT (username)
            DO UPDATE SET last_full_check = EXCLUDED.last_full_check;
        """
        with _lock:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (username, _utc_now_dt()))
                conn.commit()

    def add_domain(self, username: str, raw_domain: str) -> bool:
        ok, host, _reason = self.validate_domain(raw_domain)
        if not ok or not host:
            return False

        sql = """
            INSERT INTO public.user_domains
            (username, domain, status, ssl_expiration, ssl_issuer, added_at)
            VALUES (%s, %s, 'Pending', 'N/A', 'N/A', now())
            ON CONFLICT (username, domain) DO NOTHING;
        """
        with _lock:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (username, host))
                    inserted = (cur.rowcount == 1)
                conn.commit()
        return inserted

    def bulk_upload(self, username: str, file_path: str) -> Dict[str, Any]:
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

        added: List[str] = []
        duplicates: List[str] = []
        invalid: List[Dict[str, str]] = []

        insert_sql = """
            INSERT INTO public.user_domains
            (username, domain, status, ssl_expiration, ssl_issuer, added_at)
            VALUES (%s, %s, 'Pending', 'N/A', 'N/A', now())
            ON CONFLICT (username, domain) DO NOTHING;
        """

        with _lock:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    for raw in domains_to_add:
                        ok, normalized, reason = self.validate_domain(raw)
                        if not ok or not normalized:
                            invalid.append({"input": raw, "reason": reason or "Invalid"})
                            continue

                        cur.execute(insert_sql, (username, normalized))
                        if cur.rowcount == 1:
                            added.append(normalized)
                        else:
                            duplicates.append(normalized)

                conn.commit()

        summary = {"ok": True, "summary": {"added": added, "duplicates": duplicates, "invalid": invalid}}
        logger.info(f"Bulk upload summary for {username}: {summary}")
        return summary

    def remove_domains(self, username: str, hosts: List[str]) -> Dict[str, List[str]]:
        to_remove = {self._normalize_domain(h) for h in (hosts or []) if h and h.strip()}
        to_remove.discard("")
        to_remove_list = sorted(to_remove)

        if not to_remove_list:
            return {"removed": [], "not_found": []}

        select_sql = """
            SELECT domain
            FROM public.user_domains
            WHERE username = %s AND domain = ANY(%s);
        """
        delete_sql = """
            DELETE FROM public.user_domains
            WHERE username = %s AND domain = ANY(%s);
        """

        with _lock:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(select_sql, (username, to_remove_list))
                    existing = {row[0] for row in (cur.fetchall() or [])}
                    cur.execute(delete_sql, (username, to_remove_list))
                conn.commit()

        return {"removed": sorted(existing), "not_found": sorted(set(to_remove_list) - existing)}


if __name__ == "__main__":
    e = DomainManagementEngine()
    print("ADD:", e.add_domain("sergey", "example.com"))
    print("LIST:", e.list_domains("sergey"))
    print("REMOVE:", e.remove_domains("sergey", ["example.com", "missing.com"]))
    print("LIST AFTER:", e.list_domains("sergey"))
>>>>>>> 4cc908d (function changed to SQL methodes)
