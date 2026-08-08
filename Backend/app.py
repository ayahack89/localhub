import os

from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
)


# ============================================================
# REPOSITORY SERVICES
# ============================================================

from Backend.services.repository import (
    get_directory_contents,
    get_file,
)


# ============================================================
# ACCESS SERVICES
# ============================================================

from Backend.services.access import (
    create_request,
    get_request,
    approve_request,
    reject_request,
    get_pending_requests,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

ADMIN_PASSWORD = os.getenv(
    "LOCALHUB_ADMIN_PASSWORD"
)


# ============================================================
# CREATE FLASK APP
# ============================================================

def create_app():

    app = Flask(
        __name__,
        template_folder="../Frontend/Templates"
    )

    # Flask session secret
    app.secret_key = os.getenv(
        "LOCALHUB_SECRET_KEY",
        "localhub-development-secret"
    )


    # ========================================================
    # ACCESS CONTROL HELPER
    # ========================================================

    def require_access():

        # No request exists
        if "request_id" not in session:
            return False

        request_id = session["request_id"]

        # Get access request
        request_data = get_request(request_id)

        # Request doesn't exist
        if not request_data:
            return False

        # Only approved users can access repository
        if request_data["status"] != "approved":
            return False

        return True


    # ========================================================
    # MAIN DASHBOARD / REPOSITORY ROOT
    # ========================================================

    # Two endpoint names are intentionally supported:
    # - dashboard: used by the new access-flow code
    # - home: used by the existing LocalHub templates (base.html)
    @app.route("/", endpoint="dashboard")
    @app.route("/", endpoint="home")
    def dashboard():

        # ----------------------------------------------------
        # No access request
        # ----------------------------------------------------

        if "request_id" not in session:

            return redirect(
                url_for("login")
            )


        # ----------------------------------------------------
        # Get request
        # ----------------------------------------------------

        request_id = session["request_id"]

        request_data = get_request(request_id)


        # ----------------------------------------------------
        # Request doesn't exist
        # ----------------------------------------------------

        if not request_data:

            session.clear()

            return redirect(
                url_for("login")
            )


        status = request_data["status"]


        # ----------------------------------------------------
        # PENDING
        # ----------------------------------------------------

        if status == "pending":

            return redirect(
                url_for("pending")
            )


        # ----------------------------------------------------
        # REJECTED
        # ----------------------------------------------------

        if status == "rejected":

            return redirect(
                url_for("access_rejected")
            )


        # ----------------------------------------------------
        # APPROVED
        # ----------------------------------------------------

        if status == "approved":

            try:

                # Get repository root contents
                items = get_directory_contents()

            except PermissionError as error:

                print(
                    "Repository permission error:",
                    repr(error)
                )

                return (
                    f"Repository access denied: {error}",
                    403
                )

            except FileNotFoundError as error:

                print(
                    "Repository not found:",
                    repr(error)
                )

                return (
                    f"Repository directory not found: {error}",
                    404
                )

            except Exception as error:

                # IMPORTANT:
                # Show actual error during development
                print(
                    "Repository dashboard error:",
                    repr(error)
                )

                return (
                    f"Repository dashboard error: {error}",
                    500
                )


            # ------------------------------------------------
            # Render repository dashboard
            # ------------------------------------------------

            return render_template(
                "index.html",
                items=items,
                current_path=""
            )


        # ----------------------------------------------------
        # Unknown status
        # ----------------------------------------------------

        return (
            f"Unknown access status: {status}",
            500
        )


    # ========================================================
    # REPOSITORY DIRECTORY BROWSER
    # ========================================================

    @app.route("/repo/<path:relative_path>")
    def browse_repository(relative_path):

        # ----------------------------------------------------
        # Check access
        # ----------------------------------------------------

        if not require_access():

            return redirect(
                url_for("login")
            )


        # ----------------------------------------------------
        # Get directory contents
        # ----------------------------------------------------

        try:

            items = get_directory_contents(
                relative_path
            )

        except PermissionError as error:

            print(
                "Repository permission error:",
                repr(error)
            )

            return (
                f"Access denied: {error}",
                403
            )

        except FileNotFoundError as error:

            print(
                "Directory not found:",
                repr(error)
            )

            return (
                f"Directory not found: {error}",
                404
            )

        except NotADirectoryError as error:

            print(
                "Not a directory:",
                repr(error)
            )

            return (
                f"Not a directory: {error}",
                400
            )

        except Exception as error:

            print(
                "Repository browser error:",
                repr(error)
            )

            return (
                f"Repository browser error: {error}",
                500
            )


        # ----------------------------------------------------
        # Render repository directory
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Check access
        # ----------------------------------------------------

        if not require_access():

            return redirect(
                url_for("login")
            )


        # ----------------------------------------------------
        # Get requested file
        # ----------------------------------------------------

        try:

            file_path = get_file(
                relative_path
            )

        except PermissionError as error:

            print(
                "File permission error:",
                repr(error)
            )

            return (
                f"Access denied: {error}",
                403
            )

        except FileNotFoundError as error:

            print(
                "File not found:",
                repr(error)
            )

            return (
                f"File not found: {error}",
                404
            )

        except IsADirectoryError as error:

            print(
                "Directory requested as file:",
                repr(error)
            )

            return (
                f"This is a directory: {error}",
                400
            )

        except Exception as error:

            print(
                "File access error:",
                repr(error)
            )

            return (
                f"Internal file error: {error}",
                500
            )


        # ----------------------------------------------------
        # Try reading as text
        # ----------------------------------------------------

        try:

            content = file_path.read_text(
                encoding="utf-8"
            )

        except UnicodeDecodeError:

            # Binary file
            return send_file(
                file_path,
                as_attachment=True
            )


        # ----------------------------------------------------
        # Render text file
        # ----------------------------------------------------

        return render_template(
            "file_view.html",
            content=content,
            file_name=file_path.name
        )


    # ========================================================
    # LOGIN / REQUEST ACCESS
    # ========================================================

    @app.route(
        "/login",
        methods=["GET", "POST"]
    )
    def login():

        # ----------------------------------------------------
        # Submit access request
        # ----------------------------------------------------

        if request.method == "POST":

            username = request.form.get(
                "username",
                ""
            ).strip()


            # Empty username
            if not username:

                return (
                    "Username is required",
                    400
                )


            # ------------------------------------------------
            # Create request
            # ------------------------------------------------

            request_id = create_request(
                username
            )


            # ------------------------------------------------
            # Save request ID in session
            # ------------------------------------------------

            session["request_id"] = request_id


            # ------------------------------------------------
            # Go to pending page
            # ------------------------------------------------

            return redirect(
                url_for("pending")
            )


        # ----------------------------------------------------
        # Show login page
        # ----------------------------------------------------

        return render_template(
            "login.html"
        )


    # ========================================================
    # WAITING FOR APPROVAL
    # ========================================================

    @app.route("/pending")
    def pending():

        # ----------------------------------------------------
        # No request
        # ----------------------------------------------------

        if "request_id" not in session:

            return redirect(
                url_for("login")
            )


        request_id = session["request_id"]

        request_data = get_request(
            request_id
        )


        # ----------------------------------------------------
        # Request doesn't exist
        # ----------------------------------------------------

        if not request_data:

            session.clear()

            return redirect(
                url_for("login")
            )


        status = request_data["status"]


        # ----------------------------------------------------
        # APPROVED
        # ----------------------------------------------------

        if status == "approved":

            return redirect(
                url_for("dashboard")
            )


        # ----------------------------------------------------
        # REJECTED
        # ----------------------------------------------------

        if status == "rejected":

            return redirect(
                url_for("access_rejected")
            )


        # ----------------------------------------------------
        # PENDING
        # ----------------------------------------------------

        return render_template(
            "pending.html",
            username=request_data["username"]
        )


    # ========================================================
    # ACCESS REJECTED
    # ========================================================

    @app.route("/rejected")
    def access_rejected():

        # ----------------------------------------------------
        # No request
        # ----------------------------------------------------

        if "request_id" not in session:

            return redirect(
                url_for("login")
            )


        request_id = session["request_id"]

        request_data = get_request(
            request_id
        )


        # ----------------------------------------------------
        # Request doesn't exist
        # ----------------------------------------------------

        if not request_data:

            session.clear()

            return redirect(
                url_for("login")
            )


        status = request_data["status"]


        # ----------------------------------------------------
        # Still pending
        # ----------------------------------------------------

        if status == "pending":

            return redirect(
                url_for("pending")
            )


        # ----------------------------------------------------
        # Somehow approved
        # ----------------------------------------------------

        if status == "approved":

            return redirect(
                url_for("dashboard")
            )


        # ----------------------------------------------------
        # Rejected
        # ----------------------------------------------------

        return render_template(
            "rejected.html"
        )


    # ========================================================
    # REQUEST STATUS API
    # ========================================================

    @app.route("/api/request-status")
    def request_status():

        # ----------------------------------------------------
        # No request
        # ----------------------------------------------------

        if "request_id" not in session:

            return {
                "status": "unauthorized"
            }, 401


        request_id = session["request_id"]

        request_data = get_request(
            request_id
        )


        # ----------------------------------------------------
        # Request doesn't exist
        # ----------------------------------------------------

        if not request_data:

            return {
                "status": "not_found"
            }, 404


        # ----------------------------------------------------
        # Return current status
        # ----------------------------------------------------

        return {
            "status": request_data["status"]
        }


    # ========================================================
    # ADMIN LOGIN
    # ========================================================

    @app.route(
        "/admin/login",
        methods=["GET", "POST"]
    )
    def admin_login():

        # ----------------------------------------------------
        # Login attempt
        # ----------------------------------------------------

        if request.method == "POST":

            password = request.form.get(
                "password",
                ""
            )


            # ------------------------------------------------
            # Validate password
            # ------------------------------------------------

            if (
                ADMIN_PASSWORD
                and password == ADMIN_PASSWORD
            ):

                session["is_admin"] = True

                return redirect(
                    url_for("admin")
                )


            # ------------------------------------------------
            # Invalid password
            # ------------------------------------------------

            return render_template(
                "admin_login.html",
                error="Invalid password"
            )


        # ----------------------------------------------------
        # Show admin login
        # ----------------------------------------------------

        return render_template(
            "admin_login.html"
        )


    # ========================================================
    # ADMIN DASHBOARD
    # ========================================================

    @app.route("/admin")
    def admin():

        # ----------------------------------------------------
        # Only admin
        # ----------------------------------------------------

        if not session.get("is_admin"):

            return redirect(
                url_for("admin_login")
            )


        # ----------------------------------------------------
        # Get pending requests
        # ----------------------------------------------------

        requests = get_pending_requests()


        # ----------------------------------------------------
        # Render admin dashboard
        # ----------------------------------------------------

        return render_template(
            "admin.html",
            requests=requests
        )


    # ========================================================
    # APPROVE REQUEST
    # ========================================================

    @app.route(
        "/admin/approve/<request_id>"
    )
    def approve(request_id):

        # ----------------------------------------------------
        # Admin authentication
        # ----------------------------------------------------

        if not session.get("is_admin"):

            return redirect(
                url_for("admin_login")
            )


        # ----------------------------------------------------
        # Approve request
        # ----------------------------------------------------

        success = approve_request(
            request_id
        )


        # ----------------------------------------------------
        # Request not found
        # ----------------------------------------------------

        if not success:

            return (
                "Request not found",
                404
            )


        # ----------------------------------------------------
        # Back to admin dashboard
        # ----------------------------------------------------

        return redirect(
            url_for("admin")
        )


    # ========================================================
    # REJECT REQUEST
    # ========================================================

    @app.route(
        "/admin/reject/<request_id>"
    )
    def reject(request_id):

        # ----------------------------------------------------
        # Admin authentication
        # ----------------------------------------------------

        if not session.get("is_admin"):

            return redirect(
                url_for("admin_login")
            )


        # ----------------------------------------------------
        # Reject request
        # ----------------------------------------------------

        success = reject_request(
            request_id
        )


        # ----------------------------------------------------
        # Request not found
        # ----------------------------------------------------

        if not success:

            return (
                "Request not found",
                404
            )


        # ----------------------------------------------------
        # Back to admin dashboard
        # ----------------------------------------------------

        return redirect(
            url_for("admin")
        )


    # ========================================================
    # RETURN FLASK APP
    # ========================================================

    return app