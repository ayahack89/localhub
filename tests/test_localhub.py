import os
import shutil
import tempfile
import unittest
from pathlib import Path

from Backend.services.repository import (
    set_repository_root,
    get_repository_root,
    get_directory_contents,
    get_file,
)
from Backend.services.access import (
    create_request,
    get_request,
    approve_request,
    reject_request,
    get_pending_requests,
    clear_all_requests,
)
from Backend.services.session import SessionService
from Backend.app import create_app


class TestLocalHub(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        (self.repo_path / "sample.txt").write_text("hello world", encoding="utf-8")
        (self.repo_path / "subfolder").mkdir()
        (self.repo_path / "subfolder" / "helper.py").write_text("print('sub')", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dynamic_repository_root(self):
        set_repository_root(self.repo_path)
        self.assertEqual(get_repository_root(), self.repo_path.resolve())

        contents = get_directory_contents()
        names = [item["name"] for item in contents]
        self.assertIn("sample.txt", names)
        self.assertIn("subfolder", names)

        file_p = get_file("sample.txt")
        self.assertTrue(file_p.exists())
        self.assertEqual(file_p.read_text(encoding="utf-8"), "hello world")

    def test_path_traversal_prevention(self):
        set_repository_root(self.repo_path)
        with self.assertRaises(PermissionError):
            get_directory_contents("../")

        with self.assertRaises(PermissionError):
            get_file("../../etc/passwd")

    def test_access_control_workflow(self):
        clear_all_requests()

        req_id = create_request("Alice")
        self.assertIsNotNone(req_id)

        req = get_request(req_id)
        self.assertEqual(req["username"], "Alice")
        self.assertEqual(req["status"], "pending")

        pending = get_pending_requests()
        self.assertEqual(len(pending), 1)

        approve_success = approve_request(req_id)
        self.assertTrue(approve_success)

        req_after = get_request(req_id)
        self.assertEqual(req_after["status"], "approved")
        self.assertEqual(len(get_pending_requests()), 0)

    def test_flask_app_routes(self):
        app = create_app(repo_path=self.repo_path)
        client = app.test_client()

        # 1. Unauthenticated root redirect
        res = client.get("/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

        # 2. Submit access request
        res = client.post("/login", data={"username": "Bob"})
        self.assertEqual(res.status_code, 302)
        self.assertIn("/pending", res.headers["Location"])

        # 3. Check status API
        res = client.get("/api/request-status")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["status"], "pending")

        # 4. Admin Auth
        session_info = SessionService.get_session()
        token = session_info["admin_token"]
        res = client.get(f"/admin/auth?token={token}")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/admin", res.headers["Location"])

        # 5. Admin data API
        res = client.get("/api/admin/data")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["pending_count"], 1)

        # 6. Approve Bob
        pending_id = res.json["pending_requests"][0]["id"]
        res = client.post(f"/admin/approve/{pending_id}")
        self.assertEqual(res.status_code, 302)

        # 7. Check approved status
        res = client.get("/api/request-status")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["status"], "approved")

        # 8. Access repository root
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"sample.txt", res.data)


if __name__ == "__main__":
    unittest.main()
