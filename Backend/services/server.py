from Backend.app import create_app

class ServerService:
    @staticmethod
    def start_server(
        host="127.0.0.1",
        port=5000,
        debug=False
    ):
        app = create_app()

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
        )