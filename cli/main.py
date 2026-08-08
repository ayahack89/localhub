import typer
from Backend.utils.project import current_dir, current_path
from Backend.services.server import ServerService
from Backend.services.tunnel import TunnelService

app = typer.Typer()

@app.command()
def start():
    print("Initiated....")

    Current_dir = current_dir()
    print(f"Project Name: {Current_dir}")

    Current_path = current_path()
    print(f"Project Location: {Current_path}")

    ServerService.start_server()

@app.command()
def share():
    print("🚀 LocalHub Share")

    process, public_url = TunnelService.start_tunnel()

    if public_url:
        print(f"Public URL: {public_url}")
    else:
        print("❌ Failed to generate public URL.")


@app.command()
def stop():
    print("Terminated....")


if __name__ == "__main__":
    app()