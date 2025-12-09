from flask import Flask, request, jsonify, session, redirect, render_template
import os
from UserManagementModule import UserManager as UM
from DomainManagementEngine import DomainManagementEngine as DME
from MonitoringSystem import MonitoringSystem as MS
import logger

logger = logger.setup_logger("app")
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


# ---------------------------
# UI routes
# ---------------------------
@app.route('/', methods=['GET'])
def main_page():
    if "username" in session:
        return redirect("/dashboard")
    return app.send_static_file('main/main.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if "username" in session:
            return redirect("/dashboard")
        return app.send_static_file('login/login.html')

    data = _get_payload()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if user_manager.validate_login(username, password):
        session["username"] = username
        return jsonify({"ok": True, "message": "Login successful", "username": username}), 200

    return jsonify({"ok": False, "error": "Invalid username or password"}), 401


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return app.send_static_file('register/register.html')

    if request.method == 'GET':
        return app.send_static_file('register/register.html')
    
    try:
        # Getting Payload
        registerInfo = _get_payload()
        # Extracting username, password and password confirmation
        username = (registerInfo.get("username") or "").strip()
        password = registerInfo.get("password") or ""
        password_confirmation = registerInfo.get("password_confirmation")
        # Registering username and getting status message
        register_status = user_manager.register_page_add_user(
            username, 
            password, 
            password_confirmation, 
            domain_engine)
        # Return code, if:
        # 201 - username registered Succesfully
        # 400 - invalid fields
        # 409 - username already existing
        # 500 - internal server error
        if "error" in register_status:
            if "Username already taken." in register_status["error"]:
                return jsonify(register_status), 409
            return jsonify(register_status), 400
        # User registered successfully
        session["username"] = username
        return jsonify(register_status), 201
    except Exception as e:
        return jsonify({"error": f"User could not be registered: {str(e)}"}), 500


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if "username" not in session:
        return redirect("/login")

    username = session['username']
    domains = domain_engine.list_domains(username)

    return render_template('dashboard.html', username=username, domains=domains)


@app.route('/logout', methods=['GET'])
def logout():
    session.pop("username", None)
    return redirect("/login")


@app.route('/get_username', methods=['GET'])
def get_username():
    if "username" not in session:
        return {"error": "not logged in"}, 401
    return {"username": session["username"]}


# ---------------------------
# Domains
# ---------------------------
@app.route('/add_domain', methods=['POST'])
def add_domain():
    if "username" not in session:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    data = _get_payload()
    raw_domain = (data.get("domain") or "").strip()

    ok, norm_domain, reason = domain_engine.validate_domain(raw_domain)
    if not ok:
        return jsonify({"ok": False, "error": f"Invalid domain: {reason}"}), 400

    saved = domain_engine.add_domain(session["username"], norm_domain)
    if not saved:
        return jsonify({"ok": False, "error": "Domain already exists"}), 409

    return jsonify({"ok": True, "domain": norm_domain}), 201


@app.route('/bulk_domains', methods=['POST'])
def bulk_domains():
    if "username" not in session:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    f = request.files.get('file')
    if not f:
        return jsonify({"ok": False, "error": "File is required"}), 400

    filename = (f.filename or "").lower()
    if not filename.endswith(".txt"):
        return jsonify({"ok": False, "error": "Only .txt files are allowed"}), 400

    added, duplicates, invalid = [], [], []
    for raw in f.read().decode('utf-8', errors='ignore').splitlines():
        raw = raw.strip()
        if not raw:
            continue

        ok, domain, reason = domain_engine.validate_domain(raw)

        if not ok:
            invalid.append({"input": raw, "reason": reason})
            continue

        saved = domain_engine.add_domain(session["username"], domain)
        (added if saved else duplicates).append(domain)

    return jsonify({
        "ok": True,
        "summary": {
            "added": added,
            "duplicates": duplicates,
            "invalid": invalid
        }
    }), 200


@app.route('/remove_domains', methods=['POST'])
def remove_domains():
    if "username" not in session:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    data = _get_payload()
    domains_to_remove = data.get("domains") or []

    if not isinstance(domains_to_remove, list) or not domains_to_remove:
        return jsonify({"ok": False, "error": "Request must include a non-empty 'domains' list"}), 400

    result = domain_engine.remove_domains(session["username"], domains_to_remove)

    return jsonify({"ok": True, "summary": result}), 200


@app.route('/my_domains', methods=['GET'])
def my_domains():
    if "username" not in session:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    data = domain_engine.list_domains(session["username"])
    return jsonify({"ok": True, "data": data}), 200


# ---------------------------
# Monitoring
# ---------------------------
@app.route('/scan_domains', methods=['GET'])
def scan_domains():
    if "username" not in session:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    username = session["username"]
    try:
        updated = monitoring_system.scan_user_domains(username, dme=domain_engine)
        return jsonify({"ok": True, "updated": len(updated)}), 200
    except Exception as e:
        logger.error(f"Error during scan: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

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
    app.run(debug=True, host="0.0.0.0", port=8080)
