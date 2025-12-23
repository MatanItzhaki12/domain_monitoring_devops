from flask import Flask, request, jsonify, session, redirect, render_template
import requests
import os
import logger
from backend_client import backend_post
from backend_client import backend_get
from backend_client import backend_delete
from backend_client import BACKEND_BASE_URL

logger = logger.setup_logger("frontend")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "group2_devops_project")

# ---------------------------
# Health routes
# ---------------------------

@app.route("/ping")
def ping():
    return "pong"

@app.route("/pingbackend", methods=["GET"])
def pingbackend():
    r = requests.get("http://localhost:8080/api/ping", timeout=3)

    return jsonify(r.json()), r.status_code

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
    }), 200
    

# ---------------------------
# UI routes
# ---------------------------
@app.route('/', methods=['GET'])
def main_page():
    if "username" in session:
        return redirect("/dashboard")
    return app.send_static_file('main/main.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    # ---------- GET ----------
    if request.method == "GET":
        if "username" in session:
            return redirect("/dashboard")
        return app.send_static_file("login/login.html")

    # ---------- POST ----------
    data = request.get_json(silent=True) or {}

    resp, status = backend_post("/api/login", json=data)

    if resp.get("ok"):
        session["username"] = resp["username"]
        return jsonify({"ok": True, "username": resp["username"]}), 200

    return resp, status


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return app.send_static_file("register/register.html")

    data = request.get_json(silent=True) or {}

    resp, status = backend_post("/api/register", json=data)

    if resp.get("ok"):
        session["username"] = resp["username"]
        return resp, status

    return resp, status


@app.route("/dashboard", methods=["GET"])
def dashboard():
    # 1. Enforce login
    if "username" not in session:
        return redirect("/login")

    # 2. Fetch domains from backend
    resp, status = backend_get("/api/domains")

    # 3. Backend rejected identity → session no longer valid
    if status == 401:
        session.pop("username", None)
        return redirect("/login")

    # 4. Any other backend error
    if status != 200 or not resp.get("ok"):
        return "Failed to load dashboard", 500

    # 5. Render exactly the same template as before
    return render_template(
        "dashboard.html",
        username=session["username"],
        domains=resp.get("domains", [])
    )



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
@app.route("/add_domain", methods=["POST"])
def add_domain():
    if "username" not in session:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}

    resp, status = backend_post("/api/domains", json=data)
    return jsonify(resp), status


@app.route("/bulk_domains", methods=["POST"])
def bulk_domains():
    if "username" not in session:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    file = request.files.get("file")
    if not file:
        return jsonify({
            "ok": False,
            "error": "File is required"
        }), 400

    file_bytes = file.read()

    resp, status = backend_post(
        "/api/domains/bulk",
        files={
            "file": (file.filename, file_bytes, file.mimetype)
        }
    )

    return jsonify(resp), status



@app.route("/remove_domains", methods=["POST"])
def remove_domains():
    if "username" not in session:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}

    resp, status = backend_delete("/api/domains", json=data)

    return jsonify(resp), status


# ---------------------------
# Monitoring
# ---------------------------
@app.route("/scan_domains", methods=["POST"])
def scan_domains():
    if "username" not in session:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    resp, status = backend_post("/api/scan")
    return jsonify(resp), status


# ---------------------------
# Static passthrough
# ---------------------------
@app.route('/<filename>', methods=['GET'])
def static_files(filename):
    return app.send_static_file(filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8081)
