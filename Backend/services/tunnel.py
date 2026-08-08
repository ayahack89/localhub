import re
import subprocess

class TunnelService:
    @staticmethod

    def start_tunnel(
        host="127.0.0.1",
        port=5000,
        debug=False
    ):
        url = f"http://{host}:{port}"

        print()
        print("🌐 Starting LocalHub tunnel...")
        print(f"Forwarding: {url}")
        print()

        process = subprocess.Popen(
            [
                "cloudflared",
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

        for line in process.stdout:
             # Show Cloudflare output in terminal
            print(line, end="")

            # Look for the generated trycloudflare URL
            match = re.search(
                r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com",
                line
            )

            if match and public_url is None:

                public_url = match.group(0)

                print()
                print("=" * 60)
                print("✓ LocalHub tunnel is active")
                print("=" * 60)
                print()
                print(f"Public URL: {public_url}")
                print()
                print("Share this URL with your collaborator.")
                print()

        return process, public_url
