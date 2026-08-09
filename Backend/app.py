import os
import io
import zipfile
from pathlib import Path
from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    jsonify,
)

# ============================================================
# REPOSITORY & ACCESS & SESSION SERVICES
# ============================================================

from Backend.services.repository import (
    get_directory_contents,
    get_file,
    get_repository_root,
    set_repository_root,
)

from Backend.services.access import (
    create_request,
    get_request,
    approve_request,
    reject_request,
    get_pending_requests,
    get_approved_requests,
    get_all_requests,
)

from Backend.services.session import SessionService

# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

ADMIN_PASSWORD = os.getenv("LOCALHUB_ADMIN_PASSWORD", "admin")


# ============================================================
# CREATE FLASK APP
# ============================================================

def create_app(repo_path=None):

    backend_dir = Path(__file__).resolve().parent
    template_folder = backend_dir.parent / "Frontend" / "Templates"
    static_folder = backend_dir / "static"

    app = Flask(
        __name__,
        template_folder=str(template_folder),
        static_folder=str(static_folder)
    )

    # Flask session secret
    app.secret_key = os.getenv(
        "LOCALHUB_SECRET_KEY",
        "localhub-development-secret-key-2026"
    )

    if repo_path:
        set_repository_root(repo_path)
        SessionService.init_session(repo_path, admin_token=ADMIN_PASSWORD)
    else:
        # Initialize with current working directory if not set
        current_root = get_repository_root()
        SessionService.init_session(current_root, admin_token=ADMIN_PASSWORD)


    # ========================================================
    # ACCESS CONTROL HELPER
    # ========================================================

    def require_access():
        if "request_id" not in session:
            return False

        request_id = session["request_id"]
        request_data = get_request(request_id)

        if not request_data:
            return False

        if request_data["status"] != "approved":
            return False

        return True


    # ========================================================
    # GLOBAL TEMPLATE CONTEXT
    # ========================================================
    @app.context_processor
    def inject_global_vars():
        sess_info = SessionService.get_session()
        repo_root = get_repository_root()
        return {
            "repo_name": repo_root.name,
            "session_info": sess_info,
            "is_admin": session.get("is_admin", False)
        }


    # ========================================================
    # MAIN DASHBOARD / REPOSITORY ROOT
    # ========================================================

    @app.route("/", endpoint="dashboard")
    @app.route("/", endpoint="home")
    def dashboard():
        # Check active session status
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return render_template("session_stopped.html"), 410

        # No access request -> redirect to collaborator login
        if "request_id" not in session:
            return redirect(url_for("login"))

        request_id = session["request_id"]
        request_data = get_request(request_id)

        if not request_data:
            session.clear()
            return redirect(url_for("login"))

        status = request_data["status"]

        if status == "pending":
            return redirect(url_for("pending"))

        if status == "rejected":
            return redirect(url_for("access_rejected"))

        if status == "approved":
            try:
                items = get_directory_contents()
            except PermissionError as error:
                return f"Repository access denied: {error}", 403
            except FileNotFoundError as error:
                return f"Repository directory not found: {error}", 404
            except Exception as error:
                return f"Repository dashboard error: {error}", 500

            return render_template(
                "index.html",
                items=items,
                current_path="",
                username=request_data.get("username", "Collaborator")
            )

        return f"Unknown access status: {status}", 500


    # ========================================================
    # REPOSITORY DIRECTORY BROWSER
    # ========================================================

    @app.route("/repo/<path:relative_path>")
    def browse_repository(relative_path):
        if not require_access():
            return redirect(url_for("login"))

        try:
            items = get_directory_contents(relative_path)
        except PermissionError as error:
            return f"Access denied: {error}", 403
        except FileNotFoundError as error:
            return f"Directory not found: {error}", 404
        except NotADirectoryError as error:
            return f"Not a directory: {error}", 400
        except Exception as error:
            return f"Repository browser error: {error}", 500

        return render_template(
            "index.html",
            items=items,
            current_path=relative_path
        )


    # ========================================================
    # FILE VIEW
    # ========================================================

    @app.route("/file/<path:relative_path>")
    def view_file(relative_path):
        if not require_access():
            return redirect(url_for("login"))

        try:
            file_path = get_file(relative_path)
        except PermissionError as error:
            return f"Access denied: {error}", 403
        except FileNotFoundError as error:
            return f"File not found: {error}", 404
        except IsADirectoryError as error:
            return f"This is a directory: {error}", 400
        except Exception as error:
            return f"Internal file error: {error}", 500

        # Try reading as text
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Binary file -> send as attachment download
            return send_file(file_path, as_attachment=True)

        return render_template(
            "file_view.html",
            content=content,
            file_name=file_path.name,
            relative_path=relative_path
        )


    # ========================================================
    # FILE DOWNLOAD ENDPOINT
    # ========================================================

    @app.route("/download/<path:relative_path>")
    def download_file(relative_path):
        if not require_access():
            return redirect(url_for("login"))

        try:
            file_path = get_file(relative_path)
            return send_file(file_path, as_attachment=True)
        except Exception as error:
            return f"Download failed: {error}", 404


    # ========================================================
    # LOGIN / REQUEST ACCESS
    # ========================================================

    @app.route("/login", methods=["GET", "POST"])
    def login():
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return render_template("session_stopped.html"), 410

        if request.method == "POST":
            username = request.form.get("username", "").strip()

            if not username:
                return render_template("login.html", error="Username is required")

            request_id = create_request(username)
            session["request_id"] = request_id
            SessionService.log_activity(f"Collaborator '{username}' requested access")

            return redirect(url_for("pending"))

        return render_template("login.html")


    # ========================================================
    # WAITING FOR APPROVAL
    # ========================================================

    @app.route("/pending")
    def pending():
        if "request_id" not in session:
            return redirect(url_for("login"))

        request_id = session["request_id"]
        request_data = get_request(request_id)

        if not request_data:
            session.clear()
            return redirect(url_for("login"))

        status = request_data["status"]

        if status == "approved":
            return redirect(url_for("dashboard"))

        if status == "rejected":
            return redirect(url_for("access_rejected"))

        return render_template(
            "pending.html",
            username=request_data["username"]
        )


    # ========================================================
    # ACCESS REJECTED
    # ========================================================

    @app.route("/rejected")
    def access_rejected():
        if "request_id" not in session:
            return redirect(url_for("login"))

        request_id = session["request_id"]
        request_data = get_request(request_id)

        if not request_data:
            session.clear()
            return redirect(url_for("login"))

        status = request_data["status"]

        if status == "pending":
            return redirect(url_for("pending"))

        if status == "approved":
            return redirect(url_for("dashboard"))

        return render_template("rejected.html")


    # ========================================================
    # REQUEST STATUS API (POLLING)
    # ========================================================

    @app.route("/api/request-status")
    def request_status():
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return {"status": "stopped"}, 410

        if "request_id" not in session:
            return {"status": "unauthorized"}, 401

        request_id = session["request_id"]
        request_data = get_request(request_id)

        if not request_data:
            return {"status": "not_found"}, 404

        return {"status": request_data["status"]}


    # ========================================================
    # ADMIN TOKEN AUTHENTICATION (OWNER BROWSER AUTO-LOGIN)
    # ========================================================

    @app.route("/admin/auth")
    def admin_auth():
        token = request.args.get("token", "")
        sess_info = SessionService.get_session()

        if (token and (token == sess_info.get("admin_token") or token == ADMIN_PASSWORD)):
            session["is_admin"] = True
            SessionService.log_activity("Owner authenticated to dashboard")
            return redirect(url_for("admin"))

        return render_template("admin_login.html", error="Invalid admin auth token")


    # ========================================================
    # ADMIN LOGIN
    # ========================================================

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            password = request.form.get("password", "")
            sess_info = SessionService.get_session()

            if (
                (ADMIN_PASSWORD and password == ADMIN_PASSWORD) or
                (sess_info.get("admin_token") and password == sess_info.get("admin_token"))
            ):
                session["is_admin"] = True
                SessionService.log_activity("Owner logged in successfully")
                return redirect(url_for("admin"))

            return render_template("admin_login.html", error="Invalid owner password")

        return render_template("admin_login.html")


    # ========================================================
    # ADMIN DASHBOARD
    # ========================================================

    @app.route("/admin")
    def admin():
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))

        pending_reqs = get_pending_requests()
        approved_reqs = get_approved_requests()
        sess_info = SessionService.get_session()

        return render_template(
            "admin.html",
            requests=pending_reqs,
            approved_requests=approved_reqs,
            session_info=sess_info
        )


    # ========================================================
    # ADMIN DATA API (REAL-TIME DASHBOARD POLLING)
    # ========================================================

    @app.route("/api/admin/data")
    def admin_data():
        if not session.get("is_admin"):
            return {"error": "Unauthorized"}, 401

        sess_info = SessionService.get_session()
        pending_reqs = get_pending_requests()
        approved_reqs = get_approved_requests()

        return jsonify({
            "session": sess_info,
            "pending_requests": pending_reqs,
            "approved_requests": approved_reqs,
            "pending_count": len(pending_reqs),
            "approved_count": len(approved_reqs),
            "activities": sess_info.get("activities", [])
        })


    # ========================================================
    # APPROVE REQUEST
    # ========================================================

    @app.route("/admin/approve/<request_id>", methods=["GET", "POST"])
    def approve(request_id):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))

        req_data = get_request(request_id)
        username = req_data["username"] if req_data else "User"

        success = approve_request(request_id)

        if not success:
            return "Request not found", 404

        SessionService.log_activity(f"Approved collaborator '{username}'")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"status": "success", "message": f"Approved {username}"})

        return redirect(url_for("admin"))


    # ========================================================
    # REJECT REQUEST
    # ========================================================

    @app.route("/admin/reject/<request_id>", methods=["GET", "POST"])
    def reject(request_id):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))

        req_data = get_request(request_id)
        username = req_data["username"] if req_data else "User"

        success = reject_request(request_id)

        if not success:
            return "Request not found", 404

        SessionService.log_activity(f"Rejected access request from '{username}'")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"status": "success", "message": f"Rejected {username}"})

        return redirect(url_for("admin"))


    # ========================================================
    # STOP SESSION
    # ========================================================

    @app.route("/admin/stop", methods=["GET", "POST"])
    def stop_session_route():
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))

        SessionService.stop_session()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"status": "stopped"})

        return render_template("session_stopped.html")


    # ========================================================
    # API: CLONE REPOSITORY (FOR `localhub clone <URL>`)
    # ========================================================

    @app.route("/api/clone", methods=["GET", "POST"])
    def api_clone():
        # Validate collaborator access or admin
        req_id = request.args.get("request_id") or request.headers.get("X-LocalHub-Request-ID")
        is_approved = False

        if session.get("is_admin"):
            is_approved = True
        elif req_id:
            req = get_request(req_id)
            if req and req.get("status") == "approved":
                is_approved = True
        elif "request_id" in session:
            req = get_request(session["request_id"])
            if req and req.get("status") == "approved":
                is_approved = True

        if not is_approved:
            return jsonify({
                "error": "Unauthorized",
                "message": "Approved LocalHub session request is required to clone this repository."
            }), 401

        repo_root = get_repository_root()
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in repo_root.rglob("*"):
                # Skip internal directories (.localhub, .git, venv, pycache)
                parts = file_path.relative_to(repo_root).parts
                if any(part in [".localhub", ".git", "__pycache__", "venv", ".venv"] for part in parts):
                    continue

                if file_path.is_file():
                    arcname = file_path.relative_to(repo_root).as_posix()
                    zip_file.write(file_path, arcname=arcname)

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{repo_root.name}.zip"
        )


    # ========================================================
    # API: PUSH FOUNDATION (FOR `localhub push`)
    # ========================================================

    @app.route("/api/push", methods=["POST"])
    def api_push():
        req_id = request.args.get("request_id") or request.headers.get("X-LocalHub-Request-ID")
        if not req_id or not get_request(req_id) or get_request(req_id).get("status") != "approved":
            return jsonify({"error": "Unauthorized collaborator session"}), 401

        return jsonify({
            "status": "info",
            "message": "LocalHub commit-based synchronization protocol foundation reached. Push requires explicit owner review in V2."
        })


    # ========================================================
    # RETURN FLASK APP
    # ========================================================

    return app