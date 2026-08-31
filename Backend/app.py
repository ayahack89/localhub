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

from Backend.services.repository import (
    get_directory_contents,
    get_file,
    get_repository_root,
    set_repository_root,
    is_protected_path,
)

from Backend.services.access import (
    create_request,
    get_request,
    get_request_by_token,
    approve_request,
    reject_request,
    get_pending_requests,
    get_approved_requests,
    get_all_requests,
)

from Backend.services.session import SessionService

load_dotenv()

ADMIN_PASSWORD = os.getenv("LOCALHUB_ADMIN_PASSWORD", "admin")


def create_app(repo_path=None, port=None):
    backend_dir = Path(__file__).resolve().parent
    template_folder = backend_dir.parent / "Frontend" / "Templates"
    if not template_folder.exists():
        template_folder = backend_dir / "Templates"
    static_folder = backend_dir / "static"

    app = Flask(
        __name__,
        template_folder=str(template_folder),
        static_folder=str(static_folder)
    )

    app.secret_key = os.getenv(
        "LOCALHUB_SECRET_KEY",
        "localhub-development-secret-key-2026"
    )

    resolved_port = port or 5000
    if repo_path:
        set_repository_root(repo_path)
        sess = SessionService.get_session()
        resolved_path = str(Path(repo_path).resolve())
        if sess.get("repo_path") != resolved_path or sess.get("status") != "LIVE":
            SessionService.init_session(repo_path, port=resolved_port, admin_token=ADMIN_PASSWORD)
    else:
        current_root = get_repository_root()
        sess = SessionService.get_session()
        resolved_path = str(current_root)
        if sess.get("repo_path") != resolved_path or sess.get("status") != "LIVE":
            SessionService.init_session(current_root, port=resolved_port, admin_token=ADMIN_PASSWORD)

    def require_access():
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return False

        # Owner has unrestricted access
        if session.get("is_admin"):
            return True

        if "request_id" not in session:
            return False

        request_id = session["request_id"]
        request_data = get_request(request_id)

        if not request_data:
            return False

        return request_data.get("status") == "approved"

    @app.context_processor
    def inject_global_vars():
        sess_info = SessionService.get_session()
        repo_root = get_repository_root()
        
        current_username = None
        current_token = None
        if session.get("is_admin"):
            current_username = "Owner"
            current_token = sess_info.get("admin_token")
        elif "request_id" in session:
            req = get_request(session["request_id"])
            if req and req.get("status") == "approved":
                current_username = req.get("username")
                current_token = req.get("token") or req.get("id")

        return {
            "repo_name": repo_root.name,
            "session_info": sess_info,
            "is_admin": session.get("is_admin", False),
            "current_username": current_username,
            "current_token": current_token,
        }

    @app.route("/", endpoint="dashboard")
    @app.route("/", endpoint="home")
    def dashboard():
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return render_template("session_stopped.html"), 410

        if session.get("is_admin"):
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
                username="Owner"
            )

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

    @app.route("/repo/<path:relative_path>")
    def browse_repository(relative_path):
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return render_template("session_stopped.html"), 410

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

    @app.route("/file/<path:relative_path>")
    def view_file(relative_path):
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return render_template("session_stopped.html"), 410

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

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Serve binary files directly as attachments
            return send_file(file_path, as_attachment=True)

        return render_template(
            "file_view.html",
            content=content,
            file_name=file_path.name,
            relative_path=relative_path
        )

    @app.route("/download/<path:relative_path>")
    def download_file(relative_path):
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return render_template("session_stopped.html"), 410

        if not require_access():
            return redirect(url_for("login"))

        try:
            file_path = get_file(relative_path)
            return send_file(file_path, as_attachment=True)
        except PermissionError as error:
            return f"Access denied: {error}", 403
        except Exception as error:
            return f"Download failed: {error}", 404

    @app.route("/login", methods=["GET", "POST"])
    def login():
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return render_template("session_stopped.html"), 410

        # Allow collaborators to reset and submit a new request
        if request.args.get("reset"):
            session.pop("request_id", None)

        if request.method == "POST":
            username = request.form.get("username", "").strip()

            if not username:
                return render_template("login.html", error="Username is required")

            request_id = create_request(username, session_id=sess_info.get("session_id"))
            session["request_id"] = request_id
            SessionService.log_activity(f"Collaborator '{username}' requested access")

            return redirect(url_for("pending"))

        if session.get("is_admin"):
            return redirect(url_for("dashboard"))

        if "request_id" in session:
            req = get_request(session["request_id"])
            if req:
                if req["status"] == "approved":
                    return redirect(url_for("dashboard"))
                elif req["status"] == "pending":
                    return redirect(url_for("pending"))
                elif req["status"] == "rejected":
                    # Clear rejected request so collaborator can enter a new username
                    session.pop("request_id", None)

        return render_template("login.html")

    @app.route("/pending")
    def pending():
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return render_template("session_stopped.html"), 410

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

    @app.route("/rejected")
    def access_rejected():
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return render_template("session_stopped.html"), 410

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

    @app.route("/api/request-status")
    def request_status():
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return {"status": "stopped"}, 410

        token = request.args.get("token") or request.headers.get("X-LocalHub-Token")
        req_id = request.args.get("request_id") or request.headers.get("X-LocalHub-Request-ID")

        request_data = None
        if token:
            request_data = get_request_by_token(token) or get_request(token)
        elif req_id:
            request_data = get_request(req_id)
        elif "request_id" in session:
            request_data = get_request(session["request_id"])
        elif session.get("is_admin"):
            return {"status": "approved", "role": "owner"}

        if not request_data:
            return {"status": "unauthorized"}, 401

        return {
            "status": request_data["status"],
            "username": request_data.get("username", "")
        }

    @app.route("/admin/auth")
    def admin_auth():
        token = request.args.get("token", "")
        sess_info = SessionService.get_session()

        if (token and ((sess_info.get("admin_token") and token == sess_info.get("admin_token")) or (ADMIN_PASSWORD and token == ADMIN_PASSWORD))):
            session["is_admin"] = True
            SessionService.log_activity("Owner authenticated to dashboard")
            return redirect(url_for("admin"))

        return render_template("admin_login.html", error="Invalid admin auth token"), 401

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

            return render_template("admin_login.html", error="Invalid owner password"), 401

        if session.get("is_admin"):
            return redirect(url_for("admin"))

        return render_template("admin_login.html")

    @app.route("/admin")
    def admin():
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))

        sess_info = SessionService.get_session()
        pending_reqs = get_pending_requests(session_id=sess_info.get("session_id"))
        approved_reqs = get_approved_requests(session_id=sess_info.get("session_id"))

        return render_template(
            "admin.html",
            requests=pending_reqs,
            approved_requests=approved_reqs,
            session_info=sess_info
        )

    @app.route("/api/admin/data")
    def admin_data():
        if not session.get("is_admin"):
            return {"error": "Unauthorized"}, 401

        sess_info = SessionService.get_session()
        pending_reqs = get_pending_requests(session_id=sess_info.get("session_id"))
        approved_reqs = get_approved_requests(session_id=sess_info.get("session_id"))

        return jsonify({
            "session": sess_info,
            "pending_requests": pending_reqs,
            "approved_requests": approved_reqs,
            "pending_count": len(pending_reqs),
            "approved_count": len(approved_reqs),
            "activities": sess_info.get("activities", [])
        })

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

    @app.route("/admin/stop", methods=["GET", "POST"])
    def stop_session_route():
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))

        SessionService.stop_session()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"status": "stopped"})

        return render_template("session_stopped.html")

    @app.route("/api/clone", methods=["GET", "POST"])
    def api_clone():
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return jsonify({
                "error": "Session stopped",
                "message": "The Localhub collaboration session has been stopped."
            }), 410

        token = request.args.get("token") or request.headers.get("X-LocalHub-Token")
        req_id = request.args.get("request_id") or request.headers.get("X-LocalHub-Request-ID")
        admin_token = sess_info.get("admin_token")

        authenticated_user = None

        if session.get("is_admin") or (token and admin_token and token == admin_token) or (token and ADMIN_PASSWORD and token == ADMIN_PASSWORD):
            authenticated_user = "Owner"
        elif req_id:
            req = get_request(req_id)
            if req and req.get("status") == "approved":
                authenticated_user = req.get("username")
        elif token:
            req = get_request_by_token(token) or get_request(token)
            if req and req.get("status") == "approved":
                authenticated_user = req.get("username")
        elif "request_id" in session:
            req = get_request(session["request_id"])
            if req and req.get("status") == "approved":
                authenticated_user = req.get("username")

        if not authenticated_user:
            return jsonify({
                "error": "Unauthorized",
                "message": "Approved Localhub session request is required to clone this repository."
            }), 401

        if authenticated_user == "Owner":
            SessionService.log_activity("Owner cloned the repository")
        else:
            SessionService.log_activity(f"Collaborator '{authenticated_user}' cloned the repository")

        repo_root = get_repository_root()
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in repo_root.rglob("*"):
                # Exclude internal metadata and sensitive files (.git, .env, venv, etc.)
                if is_protected_path(file_path, repo_root):
                    continue

                if file_path.is_file():
                    try:
                        arcname = file_path.relative_to(repo_root).as_posix()
                        zip_file.write(file_path, arcname=arcname)
                    except ValueError:
                        continue

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{repo_root.name}.zip"
        )

    @app.route("/api/push", methods=["POST"])
    def api_push():
        sess_info = SessionService.get_session()
        if sess_info.get("status") == "STOPPED":
            return jsonify({"error": "Session stopped"}), 410

        token = request.args.get("token") or request.headers.get("X-LocalHub-Token")
        req_id = request.args.get("request_id") or request.headers.get("X-LocalHub-Request-ID")
        
        is_authorized = False
        if session.get("is_admin"):
            is_authorized = True
        elif req_id:
            req = get_request(req_id)
            if req and req.get("status") == "approved":
                is_authorized = True
        elif token:
            req = get_request_by_token(token) or get_request(token)
            if req and req.get("status") == "approved":
                is_authorized = True
        elif "request_id" in session:
            req = get_request(session["request_id"])
            if req and req.get("status") == "approved":
                is_authorized = True

        if not is_authorized:
            return jsonify({"error": "Unauthorized collaborator session"}), 401

        return jsonify({
            "status": "info",
            "message": "Localhub commit-based synchronization protocol foundation reached. Push requires explicit owner review in V2."
        })

    return app