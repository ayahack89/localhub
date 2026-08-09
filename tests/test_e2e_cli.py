import os
import time
import shutil
import unittest
import requests
from pathlib import Path

from Backend.app import create_app
from Backend.services.session import SessionService
from Backend.services.repository import set_repository_root


class TestE2EFlow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.demo_dir = Path(__file__).resolve().parent.parent / "demo-app"
        cls.cloned_dir = Path(__file__).resolve().parent.parent / "test-cloned-app"
        shutil.rmtree(cls.cloned_dir, ignore_errors=True)

    def test_full_collaboration_and_clone_flow(self):
        # 1. Create Flask app with demo-app repository root
        app = create_app(repo_path=self.demo_dir)
        client = app.test_client()

        # 2. Collaborator requests access
        res = client.post("/login", data={"username": "E2ETester"})
        self.assertEqual(res.status_code, 302)

        # 3. Verify status is pending
        res = client.get("/api/request-status")
        self.assertEqual(res.json["status"], "pending")

        # 4. Admin logs in with active admin token
        session_info = SessionService.get_session()
        admin_token = session_info["admin_token"]
        res = client.get(f"/admin/auth?token={admin_token}")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/admin", res.headers["Location"])

        # 5. Admin approves collaborator
        admin_data = client.get("/api/admin/data").json
        self.assertEqual(admin_data["pending_count"], 1)
        pending_id = admin_data["pending_requests"][0]["id"]

        client.post(f"/admin/approve/{pending_id}")

        # 6. Verify collaborator is approved
        res = client.get("/api/request-status")
        self.assertEqual(res.json["status"], "approved")

        # 7. Test repo root browsing
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"app.py", res.data)
        self.assertIn(b"README.md", res.data)

        # 8. Test subdirectory browsing
        res = client.get("/repo/src")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"main.py", res.data)

        # 9. Test file view
        res = client.get("/file/src/main.py")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"run_app", res.data)

        # 10. Test clone API
        res = client.get(f"/api/clone?request_id={pending_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["Content-Type"], "application/zip")
        self.assertTrue(len(res.data) > 100)

        # 11. Test stop session
        client.post("/admin/stop")
        res = client.get("/api/request-status")
        self.assertEqual(res.status_code, 410)

    @classmethod
    def tearDownClass(cls):
        if cls.cloned_dir.exists():
            shutil.rmtree(cls.cloned_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
