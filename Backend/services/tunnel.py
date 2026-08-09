import re
import time
import shutil
import subprocess
import threading
from Backend.services.session import SessionService

class TunnelService:
    _tunnel_process = None

    @classmethod
    def start_tunnel(cls, host="127.0.0.1", port=5000):
        url = f"http://{host}:{port}"

        cloudflared_path = shutil.which("cloudflared")
        if not cloudflared_path:
            print("⚠️ 'cloudflared' binary not found. Running in local-only mode.")
            print(f"Local Server available at: {url}")
            return None, None

        print()
        print("🌐 Initializing LocalHub public tunnel...")
        print(f"Forwarding local address: {url}")

        try:
            cls._tunnel_process = subprocess.Popen(
                [
                    cloudflared_path,
                    "tunnel",
                    "--url",
                    url
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            public_url = None
            start_time = time.time()
            timeout = 15  # wait up to 15 seconds for URL

            while time.time() - start_time < timeout:
                line = cls._tunnel_process.stdout.readline()
                if not line and cls._tunnel_process.poll() is not None:
                    break

                match = re.search(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com", line)
                if match:
                    public_url = match.group(0)
                    SessionService.set_public_url(public_url)
                    break

            if public_url:
                print("=" * 60)
                print("✓ LocalHub public tunnel active!")
                print("=" * 60)
                print(f"Public Share URL: {public_url}")
                print("Share this temporary URL with collaborators.")
                print("=" * 60)
                print()

                # Launch background thread to consume remaining tunnel logs
                def consume_logs():
                    try:
                        for _ in cls._tunnel_process.stdout:
                            pass
                    except Exception:
                        pass

                threading.Thread(target=consume_logs, daemon=True).start()
                return cls._tunnel_process, public_url
            else:
                print("⚠️ Tunnel started but URL generation timed out. Proceeding with local URL.")
                return cls._tunnel_process, None

        except Exception as e:
            print(f"❌ Failed to start cloudflared tunnel: {e}")
            return None, None

    @classmethod
    def stop_tunnel(cls):
        if cls._tunnel_process:
            try:
                cls._tunnel_process.terminate()
                cls._tunnel_process.wait(timeout=3)
            except Exception:
                pass
            cls._tunnel_process = None
