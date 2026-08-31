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
        collab_client = app.test_client()
        admin_client = app.test_client()

        # 2. Collaborator requests access
        res = collab_client.post("/login", data={"username": "E2ETester"})
        self.assertEqual(res.status_code, 302)

        # 3. Verify status is pending
        res = collab_client.get("/api/request-status")
        self.assertEqual(res.json["status"], "pending")

        # 4. Admin logs in with active admin token
        session_info = SessionService.get_session()
        admin_token = session_info["admin_token"]
        res = admin_client.get(f"/admin/auth?token={admin_token}")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/admin", res.headers["Location"])

        # 4b. Verify Owner can click 'Open Repo' directly without creating access request
        owner_repo_res = admin_client.get("/")
        self.assertEqual(owner_repo_res.status_code, 200)
        self.assertIn(b"app.py", owner_repo_res.data)
        self.assertIn(b"Owner", owner_repo_res.data)

        # 5. Admin approves collaborator
        admin_data = admin_client.get("/api/admin/data").json
        self.assertEqual(admin_data["pending_count"], 1)
        pending_req = admin_data["pending_requests"][0]
        pending_id = pending_req["id"]
        pending_token = pending_req["token"]

        admin_client.post(f"/admin/approve/{pending_id}")

        # 6. Verify collaborator is approved
        res = collab_client.get("/api/request-status")
        self.assertEqual(res.json["status"], "approved")

        # 7. Test repo root browsing and collaborator name display
        res = collab_client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"app.py", res.data)
        self.assertIn(b"README.md", res.data)
        self.assertIn(b"E2ETester", res.data)

        # 8. Test subdirectory browsing
        res = collab_client.get("/repo/src")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"main.py", res.data)

        # 9. Test file view
        res = collab_client.get("/file/src/main.py")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"run_app", res.data)

        # 10. Test clone API with token (without second approval)
        res = collab_client.get(f"/api/clone?token={pending_token}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["Content-Type"], "application/zip")
        self.assertTrue(len(res.data) > 100)

        # 11. Test stop session
        admin_client.post("/admin/stop")
        res = collab_client.get("/api/request-status")
        self.assertEqual(res.status_code, 410)

    @classmethod
    def tearDownClass(cls):
        if cls.cloned_dir.exists():
            shutil.rmtree(cls.cloned_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
