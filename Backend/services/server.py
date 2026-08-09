from Backend.app import create_app

class ServerService:
    @staticmethod
    def start_server(
        host="127.0.0.1",
        port=5000,
        debug=False,
        repo_path=None
    ):
        app = create_app(repo_path=repo_path)

        print("=" * 50)
        print("🚀 LocalHub Server Activated")
        print("=" * 50)
        print(f"Dashboard : http://{host}:{port}")
        print("Status    : Initiated...")
        print("=" * 50)

        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False
        )