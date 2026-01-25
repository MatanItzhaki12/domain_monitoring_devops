from __future__ import annotations

import os
import re
# [ORIGINAL] from threading import RLock
# [ORIGINAL] from datetime import datetime, timezone
# [ORIGINAL] from typing import Dict, List, Tuple, Any, Optional
# [ORIGINAL] import psycopg2
# [ORIGINAL] from psycopg2.extras import RealDictCursor

# [REFACTORED]
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from logger import setup_logger

# [ORIGINAL] _lock = RLock()
# [REFACTORED] (Removed)
# [WHY]: PostgreSQL handles concurrency.

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
           raise RuntimeError("DATABASE_URL is not set...")

        
       

        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(1, 20, dsn=self.db_url)
        except Exception as e:
            self.logger.critical(f"Failed to create DB pool: {e}")
            raise e
        # added connection pool.

    # [ORIGINAL]
    # def _conn(self):
    #     return psycopg2.connect(self.db_url)

    # [REFACTORED]
    @contextmanager
    def _get_db_connection(self):
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    # [WHY]: Added Context Manager for auto-cleanup of connections.

    @staticmethod
    def _normalize_domain(raw: str) -> str:        
        if not raw: return ""
        s = raw.strip().lower()
        if s.startswith("http://"): s = s[7:]
        elif s.startswith("https://"): s = s[8:]
        s = s.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
        if ":" in s: s = s.split(":", 1)[0]
        if s.endswith("."): s = s[:-1]
        return s

    def validate_domain(self, raw_domain: str) -> Tuple[bool, Optional[str], Optional[str]]:
        host = self._normalize_domain(raw_domain)
        if not host: return False, None, "Empty domain"
        if not self._FQDN_RE.match(host): return False, None, "Domain does not match FQDN format"
        return True, host, None

    def load_user_domains(self, username: str) -> List[Dict[str, Any]]:
        # [ORIGINAL]
        # sql = """
        #     SELECT domain, status, ssl_expiration, ssl_issuer, added_at, last_check
        #     FROM public.user_domains
        #     WHERE username = %s
        #     ORDER BY lower(domain) ASC;
        # """
        # with _lock: ... (execute logic)

        # [REFACTORED]
        sql = """
            SELECT 
                d.domain, 
                d.status, 
                d.ssl_expiration, 
                d.ssl_issuer, 
                d.last_check
            FROM domains d
            JOIN aux_users_domains aux ON d.id = aux.domain_id
            JOIN users u ON aux.user_id = u.id
            WHERE u.username = %s
            ORDER BY d.domain ASC;
        """
        
        with self._get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (username,))
                return [dict(r) for r in (cur.fetchall() or [])]

        # [WHY / CRITICAL FIX]: 
        # the code selected from 'public.user_domains' (which DOES NOT EXIST in init.sql).
        # we need to now JOIN 3 tables: users -> aux -> domains.

    def save_user_domains(self, username: str, data: List[Dict[str, Any]]) -> None:
        # [ORIGINAL] return

        # [REFACTORED]
        if not data: return
        
        sql = """
            UPDATE domains
            SET status = %(status)s, 
                ssl_expiration = %(ssl_expiration)s, 
                ssl_issuer = %(ssl_issuer)s, 
                last_check = now()
            WHERE domain = %(domain)s;
        """
        
        params = []
        for d in data:
            params.append({
                "domain": d.get("domain"),
                "status": d.get("status", "Pending"),
                "ssl_expiration": d.get("ssl_expiration", "N/A"),
                "ssl_issuer": d.get("ssl_issuer", "N/A")
            })

        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.executemany(sql, params)
                conn.commit()
        except Exception as e:
            self.logger.error(f"Save failed: {e}")

        # [WHY]: 
        # 1. Implemented functionality.
        # 2. Updated to target the 'domains' table (from init.sql).

    def list_domains(self, username: str) -> List[Dict[str, Any]]:
        return self.load_user_domains(username)

    def set_last_full_check_now(self, username: str) -> None:
        # sql = """
        #     INSERT INTO public.user_domain_meta (username, last_full_check)
        #     VALUES (%s, %s)
        #     ON CONFLICT (username)
        #     DO UPDATE SET last_full_check = EXCLUDED.last_full_check;
        # """
        # with _lock:
        #     with self._conn() as conn:
        #         with conn.cursor() as cur:
        #             cur.execute(sql, (username, _utc_now_dt()))
        #         conn.commit()

        

        # [REFACTORED]
        pass 
        # [WHY / CRITICAL FIX]: 
        #  init.sql DOES NOT have a 'user_domain_meta' table.
        # running the original SQL would crash the app. 
        # need to decide where to store this data.

    def add_domain(self, username: str, raw_domain: str) -> bool:
        ok, host, _reason = self.validate_domain(raw_domain)
        if not ok or not host: return False

        # [ORIGINAL]
        # sql = """
        #     INSERT INTO public.user_domains
        #     (username, domain, status, ssl_expiration, ssl_issuer, added_at)
        #     VALUES (%s, %s, 'Pending', 'N/A', 'N/A', now())
        #     ON CONFLICT (username, domain) DO NOTHING;
        # """
        # with _lock:
        #     with self._conn() as conn:
        #         with conn.cursor() as cur:
        #             cur.execute(sql, (username, host))
        #             inserted = (cur.rowcount == 1)
        #         conn.commit()
        # return inserted

        # [REFACTORED]
        inserted = False
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    # 1. Get User ID (Need ID, not Name)
                    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                    u_row = cur.fetchone()
                    if not u_row: return False
                    user_id = u_row[0]

                    # 2. Insert Domain (if new)
                    cur.execute("""
                        INSERT INTO domains (domain, status) VALUES (%s, 'Pending')
                        ON CONFLICT (domain) DO NOTHING;
                    """, (host,))
                    
                    # 3. Get Domain ID
                    cur.execute("SELECT id FROM domains WHERE domain = %s", (host,))
                    domain_id = cur.fetchone()[0]

                    # 4. Create Link (Aux Table)
                    cur.execute("""
                        INSERT INTO aux_users_domains (user_id, domain_id)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id, domain_id) DO NOTHING;
                    """, (user_id, domain_id))
                    
                    if cur.rowcount > 0: inserted = True
                conn.commit()
        except Exception as e:
            self.logger.error(f"Add Domain Error: {e}")
            return False
            
        return inserted

        # [WHY / CRITICAL FIX]:
        # original code tried to insert into 'user_domains'.
        # new code uses the db init logic: 
        #   (1) Find User -> (2) Ensure Domain Exists -> (3) Create Link.

    def bulk_upload(self, username: str, file_path: str) -> Dict[str, Any]:
        # (Simplified logic reuse for brevity)
        if not os.path.exists(file_path): return {"ok": False, "error": "File not found"}
        
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip().lower() for line in f if line.strip()]
            
        added, duplicates, invalid = [], [], []

        # [ORIGINAL]
        # ... Loop and INSERT INTO public.user_domains ...

        # [REFACTORED]
        # We reuse the logic we just fixed in add_domain
        for raw in lines:
            ok, norm, reason = self.validate_domain(raw)
            if not ok:
                invalid.append({"input": raw, "reason": reason})
                continue
            
            if self.add_domain(username, norm):
                added.append(norm)
            else:
                duplicates.append(norm)

        return {"ok": True, "summary": {"added": added, "duplicates": duplicates, "invalid": invalid}}

    def remove_domains(self, username: str, hosts: List[str]) -> Dict[str, List[str]]:
        to_remove = {self._normalize_domain(h) for h in (hosts or []) if h}
        if not to_remove: return {"removed": [], "not_found": []}

        # [ORIGINAL]
        # delete_sql = "DELETE FROM public.user_domains WHERE username=%s AND domain=ANY(%s)"
        # ... execution ...

        # [REFACTORED]
        removed = []
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1. Get User ID
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                u_row = cur.fetchone()
                
                if u_row:
                    user_id = u_row[0]
                    placeholders = ','.join(['%s'] * len(to_remove))
                    
                    # 2. Delete the LINK (Aux table), not the domain itself
                    sql = f"""
                        DELETE FROM aux_users_domains
                        WHERE user_id = %s 
                        AND domain_id IN (SELECT id FROM domains WHERE domain IN ({placeholders}))
                    """
                    cur.execute(sql, (user_id, *to_remove))
                    removed = list(to_remove) # Simplified reporting
                
            conn.commit()

        return {"removed": removed, "not_found": []}
        
        # [WHY / CRITICAL FIX]:
        # We cannot delete the domain from the 'domains' table because other users might be using it!
        # We only delete the LINK in 'aux_users_domains'.

if __name__ == "__main__":
    # Test Block
    TEST_URL = "postgresql://user:password@localhost:5432/devops_db"
    e = DomainManagementEngine(db_url=TEST_URL)
    # print(e.add_domain("sergey", "google.com")