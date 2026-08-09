import time
import shutil
import subprocess
import threading
import requests
from pathlib import Path

def test_live_cli():
    base_dir = Path(__file__).resolve().parent.parent
    demo_dir = base_dir / "demo-app"
    cloned_dir = base_dir / "test-cloned-demo-app"

    if cloned_dir.exists():
        shutil.rmtree(cloned_dir, ignore_errors=True)

    localhub_bin = base_dir / "venv" / "bin" / "localhub"

    print("🚀 Starting LocalHub server process on port 5002...")
    server_proc = subprocess.Popen(
        [str(localhub_bin), "start", str(demo_dir), "--port", "5002", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    time.sleep(3) # Wait for server startup

    try:
        # Step 1: Launch `localhub clone` in background thread
        print("🚀 Executing `localhub clone http://127.0.0.2:5002`...")
        clone_result = {"returncode": None, "stdout": "", "stderr": ""}

        def run_clone():
            proc = subprocess.run(
                [str(localhub_bin), "clone", "http://127.0.0.1:5002", "--name", "DevAlex", "--out", "test-cloned-demo-app"],
                cwd=str(base_dir),
                capture_output=True,
                text=True
            )
            clone_result["returncode"] = proc.returncode
            clone_result["stdout"] = proc.stdout
            clone_result["stderr"] = proc.stderr

        clone_thread = threading.Thread(target=run_clone)
        clone_thread.start()

        # Step 2: Give clone request time to arrive at server
        time.sleep(2)

        # Step 3: Owner logs in and checks pending requests
        admin_session = requests.Session()
        res = admin_session.get("http://127.0.0.1:5002/admin/auth?token=SuperAdmin@2O26")
        assert res.status_code == 200

        admin_data = admin_session.get("http://127.0.0.1:5002/api/admin/data").json()
        assert admin_data["pending_count"] == 1
        pending_req = admin_data["pending_requests"][0]
        assert pending_req["username"] == "DevAlex"
        print(f"✓ Owner detected pending access request from '{pending_req['username']}'")

        # Step 4: Owner approves DevAlex
        res = admin_session.post(f"http://127.0.0.1:5002/admin/approve/{pending_req['id']}")
        assert res.status_code == 200
        print("✓ Owner approved DevAlex")

        # Step 5: Wait for clone thread to complete
        clone_thread.join(timeout=15)
        print("Clone output:\n", clone_result["stdout"])
        assert clone_result["returncode"] == 0, f"Clone failed: {clone_result['stderr']}"

        # Step 6: Verify cloned repository structure
        assert cloned_dir.exists()
        assert (cloned_dir / "app.py").exists()
        assert (cloned_dir / "README.md").exists()
        assert (cloned_dir / "src" / "main.py").exists()
        assert (cloned_dir / "src" / "utils" / "helper.py").exists()
        assert (cloned_dir / "templates" / "index.html").exists()
        assert (cloned_dir / "tests" / "test_basic.py").exists()
        assert (cloned_dir / ".localhub" / "config.json").exists()
        print("✓ All cloned files & directory structure verified successfully!")

    finally:
        server_proc.terminate()
        server_proc.wait()
        if cloned_dir.exists():
            shutil.rmtree(cloned_dir, ignore_errors=True)

if __name__ == "__main__":
    test_live_cli()
