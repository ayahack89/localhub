import os
import io
import shutil
import tempfile
import zipfile
import unittest
from pathlib import Path

from Backend.services.repository import (
    set_repository_root,
    get_repository_root,
    get_directory_contents,
    get_file,
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
    clear_all_requests,
)
from Backend.services.session import SessionService
from Backend.app import create_app


class TestSecurityAndAuth(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        (self.repo_path / "README.md").write_text("# Project", encoding="utf-8")
        (self.repo_path / "main.py").write_text("print('hello')", encoding="utf-8")
        
        # Subdirectory
        (self.repo_path / "src").mkdir()
        (self.repo_path / "src" / "utils.py").write_text("def add(a, b): return a + b", encoding="utf-8")
        
        # Sensitive/protected files
        (self.repo_path / ".env").write_text("SECRET_KEY=supersecret", encoding="utf-8")
        (self.repo_path / ".env.local").write_text("LOCAL_SECRET=abc", encoding="utf-8")
        (self.repo_path / ".git").mkdir()
        (self.repo_path / ".git" / "config").write_text("[core]\nrepositoryformatversion = 0", encoding="utf-8")
        (self.repo_path / ".localhub").mkdir()
        (self.repo_path / ".localhub" / "session.json").write_text('{"status": "LIVE"}', encoding="utf-8")
        (self.repo_path / "venv").mkdir()
        (self.repo_path / "venv" / "pyvenv.cfg").write_text("home = /usr/bin", encoding="utf-8")
        (self.repo_path / ".venv").mkdir()
        (self.repo_path / ".venv" / "pyvenv.cfg").write_text("home = /usr/bin", encoding="utf-8")

        clear_all_requests()
        self.app = create_app(repo_path=self.repo_path)
        self.client = self.app.test_client()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        clear_all_requests()

    # =========================================================================
    # 1. OWNER FULL ACCESS & BYPASS (BUG #1)
    # =========================================================================

    def test_owner_has_full_access_without_approval_or_access_request(self):
        """Owner clicking 'Open Repo' gets immediate repository view without creating access request."""
        session_info = SessionService.get_session()
        admin_token = session_info["admin_token"]

        # Owner authenticates
        auth_res = self.client.get(f"/admin/auth?token={admin_token}")
        self.assertEqual(auth_res.status_code, 302)

        # Owner clicks 'Open Repo' (GET /)
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"README.md", res.data)
        self.assertIn(b"main.py", res.data)

        # Confirm NO pending access request was created for the owner
        pending = get_pending_requests()
        self.assertEqual(len(pending), 0)

        # Owner can browse subdirectory
        res_sub = self.client.get("/repo/src")
        self.assertEqual(res_sub.status_code, 200)
        self.assertIn(b"utils.py", res_sub.data)

        # Owner can view file
        res_file = self.client.get("/file/main.py")
        self.assertEqual(res_file.status_code, 200)
        self.assertIn(b"hello", res_file.data)

        # Owner can download file
        res_dl = self.client.get("/download/main.py")
        self.assertEqual(res_dl.status_code, 200)
        res_dl.close()

    # =========================================================================
    # 2. COLLABORATOR NAME IN DASHBOARD (BUG #2)
    # =========================================================================

    def test_collaborator_name_displayed_in_dashboard(self):
        """Approved collaborator sees their name clearly rendered in the repository dashboard."""
        collab_client = self.app.test_client()
        
        # Submit access request as Rahul
        res = collab_client.post("/login", data={"username": "Rahul"})
        self.assertEqual(res.status_code, 302)

        # Owner approves Rahul
        pending = get_pending_requests()
        self.assertEqual(len(pending), 1)
        rahul_req_id = pending[0]["id"]
        approve_request(rahul_req_id)

        # Rahul visits repo dashboard (GET /)
        dash_res = collab_client.get("/")
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b"Rahul", dash_res.data)
        self.assertIn(b"Welcome,", dash_res.data)

    # =========================================================================
    # 3. CLONE WITHOUT SECOND APPROVAL & CLONE TOKEN (BUG #3)
    # =========================================================================

    def test_approved_collaborator_can_clone_without_second_approval(self):
        """Approved collaborator can clone directly using pre-approved token without another approval request."""
        # 1. Collaborator requests access
        req_id = create_request("Alice")
        req_data = get_request(req_id)
        token = req_data["token"]

        # 2. Owner approves
        approve_request(req_id)
        self.assertEqual(len(get_pending_requests()), 0)

        # 3. Collaborator clones via API using pre-approved token
        clone_client = self.app.test_client()
        res = clone_client.get(f"/api/clone?token={token}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["Content-Type"], "application/zip")

        # Verify ZIP contains valid repository files
        zip_buf = io.BytesIO(res.data)
        with zipfile.ZipFile(zip_buf, "r") as zf:
            file_list = zf.namelist()
            self.assertIn("README.md", file_list)
            self.assertIn("main.py", file_list)
            self.assertIn("src/utils.py", file_list)
            # Sensitive files must NOT be in ZIP
            self.assertNotIn(".env", file_list)
            self.assertNotIn(".git/config", file_list)
            self.assertNotIn(".localhub/session.json", file_list)

        # 4. Verify NO second pending approval request was created
        self.assertEqual(len(get_pending_requests()), 0)

        # 5. Verify activity feed logged the clone
        sess_info = SessionService.get_session()
        activity_messages = [a["message"] for a in sess_info["activities"]]
        self.assertTrue(any("Alice' cloned the repository" in msg for msg in activity_messages))

    # =========================================================================
    # 4. CLONE SECURITY & AUTHORIZATION
    # =========================================================================

    def test_unauthenticated_clone_is_rejected(self):
        """Unauthenticated clone attempt returns 401 Unauthorized."""
        res = self.client.get("/api/clone")
        self.assertEqual(res.status_code, 401)

    def test_pending_collaborator_cannot_clone(self):
        """Pending (not yet approved) collaborator cannot clone."""
        req_id = create_request("Bob")
        req_data = get_request(req_id)
        token = req_data["token"]

        res = self.client.get(f"/api/clone?token={token}")
        self.assertEqual(res.status_code, 401)

    def test_rejected_collaborator_cannot_clone(self):
        """Rejected collaborator cannot clone."""
        req_id = create_request("Eve")
        reject_request(req_id)

        req_data = get_request(req_id)
        token = req_data["token"]

        res = self.client.get(f"/api/clone?token={token}")
        self.assertEqual(res.status_code, 401)

    def test_clone_identity_cannot_be_forged(self):
        """Server uses server-validated request record, ignoring any forged client parameters."""
        req_id = create_request("LegitUser")
        approve_request(req_id)
        token = get_request(req_id)["token"]

        # Attempt to supply forged username parameter
        res = self.client.get(f"/api/clone?token={token}&username=AdminImpersonator")
        self.assertEqual(res.status_code, 200)

        # Log must record LegitUser, not AdminImpersonator
        sess_info = SessionService.get_session()
        activity_messages = [a["message"] for a in sess_info["activities"]]
        self.assertTrue(any("LegitUser' cloned the repository" in msg for msg in activity_messages))
        self.assertFalse(any("AdminImpersonator" in msg for msg in activity_messages))

    # =========================================================================
    # 5. PATH TRAVERSAL PROTECTIONS
    # =========================================================================

    def test_path_traversal_blocked_in_repository_service(self):
        """Verify get_directory_contents and get_file block path traversal attempts."""
        set_repository_root(self.repo_path)

        with self.assertRaises(PermissionError):
            get_directory_contents("../")

        with self.assertRaises(PermissionError):
            get_directory_contents("../../etc")

        with self.assertRaises(PermissionError):
            get_file("../../etc/passwd")

        with self.assertRaises(PermissionError):
            get_file("../../../etc/shadow")

    def test_path_traversal_blocked_in_flask_routes(self):
        """Path traversal via HTTP routes returns 403 Forbidden or 404 Not Found, never system files."""
        session_info = SessionService.get_session()
        self.client.get(f"/admin/auth?token={session_info['admin_token']}")

        # Attempt traversing out
        res = self.client.get("/file/..%2f..%2fetc%2fpasswd")
        self.assertIn(res.status_code, [403, 404])

        res = self.client.get("/download/..%2f..%2fetc%2fpasswd")
        self.assertIn(res.status_code, [403, 404])

        res = self.client.get("/repo/..%2f..%2f")
        self.assertIn(res.status_code, [403, 404])

    # =========================================================================
    # 6. SENSITIVE & PROTECTED FILES BLOCKED
    # =========================================================================

    def test_protected_files_blocked_from_direct_access(self):
        """Access to .env, .git, .localhub, venv is strictly blocked."""
        session_info = SessionService.get_session()
        self.client.get(f"/admin/auth?token={session_info['admin_token']}")

        # .env
        res = self.client.get("/file/.env")
        self.assertEqual(res.status_code, 403)

        # .env.local
        res = self.client.get("/file/.env.local")
        self.assertEqual(res.status_code, 403)

        # .git/config
        res = self.client.get("/file/.git/config")
        self.assertEqual(res.status_code, 403)

        # .localhub/session.json
        res = self.client.get("/file/.localhub/session.json")
        self.assertEqual(res.status_code, 403)

        # venv/pyvenv.cfg
        res = self.client.get("/file/venv/pyvenv.cfg")
        self.assertEqual(res.status_code, 403)

        # .venv/pyvenv.cfg
        res = self.client.get("/file/.venv/pyvenv.cfg")
        self.assertEqual(res.status_code, 403)

    def test_protected_files_hidden_from_directory_listing(self):
        """Directory contents listing hides all protected files/directories."""
        set_repository_root(self.repo_path)
        items = get_directory_contents()
        names = [item["name"] for item in items]

        self.assertIn("README.md", names)
        self.assertIn("main.py", names)
        self.assertIn("src", names)

        self.assertNotIn(".env", names)
        self.assertNotIn(".env.local", names)
        self.assertNotIn(".git", names)
        self.assertNotIn(".localhub", names)
        self.assertNotIn("venv", names)
        self.assertNotIn(".venv", names)

    # =========================================================================
    # 7. AUTHENTICATION & ACCESS CONTROL
    # =========================================================================

    def test_unauthenticated_user_rejected_from_owner_dashboard(self):
        """Unauthenticated visitor to /admin is redirected to /admin/login."""
        res = self.client.get("/admin")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/admin/login", res.headers["Location"])

    def test_invalid_owner_token_rejected(self):
        """Invalid admin token rejected with 401."""
        res = self.client.get("/admin/auth?token=wrong-invalid-token")
        self.assertEqual(res.status_code, 401)

    def test_collaborator_cannot_access_owner_api(self):
        """Approved collaborator cannot access admin API endpoints."""
        collab_client = self.app.test_client()
        req_id = create_request("Charlie")
        approve_request(req_id)
        collab_client.post("/login", data={"username": "Charlie"})

        # Try accessing admin data
        res = collab_client.get("/api/admin/data")
        self.assertEqual(res.status_code, 401)

    # =========================================================================
    # 8. SESSION TERMINATION
    # =========================================================================

    def test_stopped_session_terminates_all_access(self):
        """Stopping the session returns 410 for browsing, clone, and polling."""
        # Authenticate owner & approve a collaborator
        session_info = SessionService.get_session()
        self.client.get(f"/admin/auth?token={session_info['admin_token']}")
        
        req_id = create_request("David")
        approve_request(req_id)
        token = get_request(req_id)["token"]

        # Stop session
        SessionService.stop_session()

        # 1. Root dashboard returns 410
        res = self.client.get("/")
        self.assertEqual(res.status_code, 410)

        # 2. Polling API returns 410
        res = self.client.get("/api/request-status")
        self.assertEqual(res.status_code, 410)

        # 3. Clone API returns 410
        res = self.client.get(f"/api/clone?token={token}")
        self.assertEqual(res.status_code, 410)

    # =========================================================================
    # 9. SYMLINK TRAVERSAL & ADVANCED SECURITY
    # =========================================================================

    def test_symlink_traversal_blocked(self):
        """Symlinks pointing outside repository root are blocked by path validation."""
        outside_dir = tempfile.mkdtemp()
        outside_file = Path(outside_dir) / "secret.txt"
        outside_file.write_text("outside secret", encoding="utf-8")

        try:
            symlink_path = self.repo_path / "link_to_outside"
            try:
                symlink_path.symlink_to(outside_dir)
            except OSError:
                return  # Skip if OS does not permit symlinks

            set_repository_root(self.repo_path)
            with self.assertRaises(PermissionError):
                get_directory_contents("link_to_outside")

            with self.assertRaises(PermissionError):
                get_file("link_to_outside/secret.txt")
        finally:
            shutil.rmtree(outside_dir, ignore_errors=True)

    # =========================================================================
    # 10. SESSION ISOLATION
    # =========================================================================

    def test_session_isolation(self):
        """Session A and Session B have distinct session IDs and tokens; requests from A are not valid in B."""
        temp_dir_b = tempfile.mkdtemp()
        repo_b = Path(temp_dir_b)
        (repo_b / "file_b.txt").write_text("repo B content", encoding="utf-8")

        try:
            # Session A
            sess_a = SessionService.init_session(self.repo_path, admin_token="token-A")
            req_a = create_request("CollabA", session_id=sess_a["session_id"])
            approve_request(req_a)
            token_a = get_request(req_a)["token"]

            # Session B
            sess_b = SessionService.init_session(repo_b, admin_token="token-B")
            
            # Assert sessions are distinct
            self.assertNotEqual(sess_a["session_id"], sess_b["session_id"])
            self.assertNotEqual(sess_a["admin_token"], sess_b["admin_token"])
            self.assertNotEqual(sess_a["repo_path"], sess_b["repo_path"])

            # Access requests for session B should not contain pending requests for session A
            pending_b = get_pending_requests(session_id=sess_b["session_id"])
            self.assertEqual(len(pending_b), 0)

        finally:
            shutil.rmtree(temp_dir_b, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
