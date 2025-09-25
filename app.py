from flask import Flask, request, jsonify, session, redirect
import os
from UserManagementModule import UserManager as UM
from DomainManagementEngine import DomainManagementEngine as DME
import MonitoringSystem as ME
import logger

logger = logger.setup_logger("app")
user_manager = UM()
domain_engine = DME(user_manager=user_manager)
monitoring_system = ME()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "group2_devops_project")


# ---------------------------
# Helpers (no error handlers here)
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
    return app.send_static_file('main/main.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if "username" in session:
            return redirect("/dashboard")
        return app.send_static_file('login/login.html')
    else:
        data = _get_payload()
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        if UM.validate_login(username,password):
            session["username"] = username
            return jsonify({"ok": True, "message": "Login successful", "username": username}), 200
        return jsonify({"ok": False, "error": "Invalid username or password"}), 401

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return app.send_static_file('register/register.html')
    else:
        try:
            registerInfo = request.json or {}
            username = (registerInfo.get("username") or "").strip()
            password = registerInfo.get("password") or ""
            password_confirmation = registerInfo.get("password_confirmation")
            register_status = user_manager.register_page_add_user(username, password, password_confirmation)
            if "message" in register_status:
                return jsonify(register_status), 200
            elif "error" in register_status:
                return jsonify(register_status), 400
        except Exception as e:
            return jsonify({"error": f"User could not be registered: {str(e)}"}), 400

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if "username" not in session:
        return redirect("/login")
    return app.send_static_file('dashboard/dashboard.html')

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

    ok, norm_domain, reason = UM.validate_domain(raw_domain)
    if not ok:
        return jsonify({"ok": False, "error": f"Invalid domain: {reason}"}), 400

    saved = UM.add_domain(session["username"], norm_domain)
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
        ok, domain, reason = UM.validate_domain(raw)
        if not ok:
            invalid.append({"input": raw, "reason": reason})
            continue
        saved = UM.add_domain(session["username"], domain)
        (added if saved else duplicates).append(domain)

    return jsonify({"ok": True, "summary": {
        "added": added,
        "duplicates": duplicates,
        "invalid": invalid
    }}), 200


@app.route('/my_domains', methods=['GET'])
def my_domains():
    if "username" not in session:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    data = UM.load_user_domains(session["username"])
    return jsonify({"ok": True, "data": data}), 200


# ---------------------------
# Monitoring
# ---------------------------
@app.route('/refresh_checks', methods=['POST'])
def refresh_checks():
    if "username" not in session:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    ME.run_user_check_async(session["username"])
    return jsonify({"ok": True, "message": "Checks started"}), 202


# ---------------------------
# Static passthrough (top-level files)
# ---------------------------
@app.route('/<filename>', methods=['GET'])
def static_files(filename):
    return app.send_static_file(filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
