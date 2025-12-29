from flask import Flask, request, jsonify
import os
from UserManagementModule import UserManager as UM
from DomainManagementEngine import DomainManagementEngine as DME
from MonitoringSystem import MonitoringSystem as MS
import logger
from IP_Library import BACKEND_PORT

logger = logger.setup_logger("backend")
user_manager = UM()
domain_engine = DME()
monitoring_system = MS()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "group2_devops_project")


# ---------------------------
# Helpers
# ---------------------------
def _get_payload():
    """Accept JSON or HTML form-data; always return a dict."""
    data = request.get_json(silent=True)
    if data is not None:
        return data
    return (request.form or {}).to_dict()

def get_authenticated_username():
    """
    Extract authenticated username from FE → BE trusted header.
    Returns username string or None.
    """
    return request.headers.get("X-Username")

# ---------------------------
# Health routes
# ---------------------------

@app.route("/api/ping", methods=["GET"])
def ping():
    return jsonify({
        "status": "pong"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
    }), 200
    
 # ---------------------------
# UI routes
# ---------------------------   

@app.route("/api/login", methods=["POST"])
def api_login():
    # 1. Parse JSON safely
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    # 2. Basic input validation
    if not username or not password:
        return jsonify({
            "ok": False,
            "error": "username and password are required"
        }), 400

    # 3. Delegate authentication to UserManager
    if user_manager.validate_login(username, password):
        logger.info(f"API login successful: username={username}")

        # 4. Backend is the authority on identity
        return jsonify({
            "ok": True,
            "username": username
        }), 200

    # 5. Authentication failed
    logger.warning(f"API login failed: username={username}")
    return jsonify({
        "ok": False,
        "error": "Invalid username or password"
    }), 401


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    password_confirmation = data.get("password_confirmation") or ""

    if not username or not password or not password_confirmation:
        return jsonify({
            "ok": False,
            "error": "All fields are required"
        }), 400

    result = user_manager.register_page_add_user(
        username,
        password,
        password_confirmation,
        domain_engine
    )

    if "error" in result:
        # Preserve original semantics
        if "Username already taken" in result["error"]:
            return jsonify({"ok": False, "error": result["error"]}), 409

        return jsonify({"ok": False, "error": result["error"]}), 400

    return jsonify({
        "message": "Registered Successfully.",
        "ok": True,
        "username": username
        
    }), 201


# ---------------------------
# Domains
# ---------------------------

@app.route("/api/domains", methods=["GET", "POST", "DELETE"])
def api_domains():
    username = get_authenticated_username()
    if not username:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    # ---------- GET ----------
    if request.method == "GET":
        domains = domain_engine.list_domains(username)
        return jsonify({
            "ok": True,
            "domains": domains
        }), 200

    # ---------- POST (add domain) ----------
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        raw_domain = (data.get("domain") or "").strip()

        if not raw_domain:
            return jsonify({
                "ok": False,
                "error": "Domain is required"
            }), 400

        ok, norm_domain, reason = domain_engine.validate_domain(raw_domain)
        if not ok:
            return jsonify({
                "ok": False,
                "error": f"Invalid domain: {reason}"
            }), 400

        saved = domain_engine.add_domain(username, norm_domain)
        if not saved:
            return jsonify({
                "ok": False,
                "error": "Domain already exists"
            }), 409

        return jsonify({
            "ok": True,
            "domain": norm_domain
        }), 201

    # ---------- DELETE ----------
    if request.method == "DELETE":
        data = request.get_json(silent=True) or {}
        domains_to_remove = data.get("domains")

        if not isinstance(domains_to_remove, list) or not domains_to_remove:
            return jsonify({
                "ok": False,
                "error": "Request must include a non-empty 'domains' list"
            }), 400

        result = domain_engine.remove_domains(username, domains_to_remove)

        return jsonify({
            "ok": True,
            "summary": result
        }), 200
    return jsonify({
        "ok": False,
        "error": "Method not allowed"
    }), 405

@app.route("/api/scan", methods=["POST"])
def api_scan_domains():
    username = get_authenticated_username()
    if not username:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        updated = monitoring_system.scan_user_domains(username, dme=domain_engine)
        return jsonify({"ok": True, "updated": len(updated)}), 200
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
        
@app.route("/api/domains/bulk", methods=["POST"])
def api_bulk_domains():
    username = get_authenticated_username()
    if not username:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    file = request.files.get("file")
    if not file:
        return jsonify({"ok": False, "error": "File is required"}), 400

    filename = (file.filename or "").lower()
    if not filename.endswith(".txt"):
        return jsonify({"ok": False, "error": "Only .txt files are allowed"}), 400

    added, duplicates, invalid = [], [], []

    for raw in file.read().decode("utf-8", errors="ignore").splitlines():
        raw = raw.strip()
        if not raw:
            continue

        ok, domain, reason = domain_engine.validate_domain(raw)
        if not ok:
            invalid.append({"input": raw, "reason": reason})
            continue

        saved = domain_engine.add_domain(username, domain)
        (added if saved else duplicates).append(domain)

    return jsonify({
        "ok": True,
        "summary": {
            "added": added,
            "duplicates": duplicates,
            "invalid": invalid
        }
    }), 200

        
# -------------------------#
#  Reload Users to Memory  #
# -------------------------#

@app.route('/reload_users_to_memory', methods=['GET'])
def reload_users_to_memory():
    try:
        user_manager.load_users_json_to_memory()
        return jsonify({"ok": True}), 200
    except Exception as e:
        logger.error(f"Error during reloading users.json: {str(e)}")
        return jsonify({"ok": False}), 500

# ---------------------------
# Static passthrough
# ---------------------------
@app.route('/<filename>', methods=['GET'])
def static_files(filename):
    return app.send_static_file(filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=BACKEND_PORT)
