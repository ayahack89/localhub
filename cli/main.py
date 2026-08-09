import os
import sys
import time
import io
import zipfile
import threading
import webbrowser
from pathlib import Path
from typing import Optional

import typer
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from Backend.services.server import ServerService
from Backend.services.tunnel import TunnelService
from Backend.services.session import SessionService
from Backend.services.repository import set_repository_root

app = typer.Typer(
    name="localhub",
    help="LocalHub - Temporary local collaboration platform for developers.",
    add_completion=False
)

console = Console()
VERSION = "0.2.0"


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]LocalHub[/bold cyan] version [green]{VERSION}[/green]")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Show LocalHub version and exit.", callback=version_callback, is_eager=True
    )
):
    """
    LocalHub V2 CLI - Instant local repository sharing & temporary collaboration.
    """
    pass


# ============================================================
# COMMAND: START
# ============================================================

@app.command()
def start(
    path: str = typer.Argument(".", help="Path to project directory to share (defaults to current directory)."),
    port: int = typer.Option(5000, "--port", "-p", help="Port to run the local server on."),
    no_browser: bool = typer.Option(False, "--no-browser", help="Disable automatic browser opening.")
):
    """
    Start a temporary LocalHub collaboration session for the specified project directory.
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        console.print(f"[bold red]Error:[/bold red] Directory '{project_path}' does not exist.")
        raise typer.Exit(code=1)

    if not project_path.is_dir():
        console.print(f"[bold red]Error:[/bold red] Path '{project_path}' is not a directory.")
        raise typer.Exit(code=1)

    # Initialize repository root & session metadata
    set_repository_root(project_path)
    session_data = SessionService.init_session(project_path, port=port)

    local_url = session_data["local_url"]
    admin_token = session_data["admin_token"]
    owner_dashboard_url = f"{local_url}/admin/auth?token={admin_token}"

    console.print(Panel(
        f"[bold cyan]LocalHub Collaboration Session[/bold cyan]\n"
        f"[dim]Project Root:[/dim] [bold white]{project_path}[/bold white]\n"
        f"[dim]Repository Name:[/dim] [bold yellow]{project_path.name}[/bold yellow]",
        title="🚀 Starting LocalHub",
        border_style="cyan"
    ))

    # Start Flask server in background thread
    server_thread = threading.Thread(
        target=ServerService.start_server,
        kwargs={"host": "127.0.0.1", "port": port, "debug": False, "repo_path": project_path},
        daemon=True
    )
    server_thread.start()

    # Give server time to bind
    time.sleep(1)

    # Start Cloudflare Tunnel
    tunnel_proc, public_url = TunnelService.start_tunnel(host="127.0.0.1", port=port)

    # Print Clean Developer Dashboard Panel
    dashboard_table = Table(show_header=False, box=None, padding=(0, 2))
    dashboard_table.add_row("[bold cyan]Session Status:[/bold cyan]", "[bold green]● LIVE[/bold green]")
    dashboard_table.add_row("[bold cyan]Repository:[/bold cyan]", f"[bold white]{project_path.name}[/bold white]")
    dashboard_table.add_row("[bold cyan]Local Address:[/bold cyan]", f"[underline blue]{local_url}[/underline blue]")
    dashboard_table.add_row("[bold cyan]Owner Dashboard:[/bold cyan]", f"[underline magenta]{owner_dashboard_url}[/underline magenta]")
    
    if public_url:
        dashboard_table.add_row("[bold cyan]Public Share URL:[/bold cyan]", f"[bold yellow]{public_url}[/bold yellow]")
    else:
        dashboard_table.add_row("[bold cyan]Public Share URL:[/bold cyan]", "[dim red]Local-only (tunnel unavailable)[/dim red]")

    console.print(Panel(
        dashboard_table,
        title="[bold green]LocalHub Command Center[/bold green]",
        subtitle="[dim]Press Ctrl+C to end collaboration session[/dim]",
        border_style="green"
    ))

    # Auto-open browser for owner dashboard
    if not no_browser:
        console.print("[dim]Opening Owner Dashboard in default browser...[/dim]")
        webbrowser.open(owner_dashboard_url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Stopping LocalHub session...[/bold yellow]")
        SessionService.stop_session()
        TunnelService.stop_tunnel()
        console.print("[bold green]✓ LocalHub session terminated cleanly.[/bold green]")


# ============================================================
# COMMAND: STOP
# ============================================================

@app.command()
def stop():
    """
    Stop the currently running LocalHub session.
    """
    session = SessionService.get_session()
    if session and session.get("status") == "LIVE":
        local_url = session.get("local_url", "http://127.0.0.1:5000")
        admin_token = session.get("admin_token")
        try:
            requests.get(f"{local_url}/admin/stop", timeout=2)
        except Exception:
            pass
        SessionService.stop_session()
        TunnelService.stop_tunnel()
        console.print("[bold green]✓ LocalHub session stopped successfully.[/bold green]")
    else:
        # Check if local session.json exists in CWD
        cwd_session_file = Path.cwd() / ".localhub" / "session.json"
        if cwd_session_file.exists():
            SessionService.stop_session()
            console.print("[bold green]✓ LocalHub session status set to STOPPED.[/bold green]")
        else:
            console.print("[yellow]No active LocalHub session found.[/yellow]")


# ============================================================
# COMMAND: STATUS
# ============================================================

@app.command()
def status():
    """
    Display current LocalHub session status and metadata.
    """
    session = SessionService.get_session()
    status_str = session.get("status", "STOPPED")

    status_color = "green" if status_str == "LIVE" else "red"

    table = Table(title="LocalHub Session Status", border_style="cyan")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Status", f"[{status_color}]● {status_str}[/{status_color}]")
    table.add_row("Repository", session.get("repo_name") or "N/A")
    table.add_row("Path", session.get("repo_path") or str(Path.cwd()))
    table.add_row("Started At", session.get("start_time") or "N/A")
    table.add_row("Local URL", session.get("local_url") or "N/A")
    table.add_row("Public Share URL", session.get("public_url") or "None")

    console.print(table)


# ============================================================
# COMMAND: CLONE
# ============================================================

@app.command()
def clone(
    url: str = typer.Argument(..., help="The temporary LocalHub public share URL or local URL."),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Your collaborator name/identity."),
    destination: Optional[str] = typer.Option(None, "--out", "-o", help="Target folder name to extract project into.")
):
    """
    Clone a repository snapshot from an active LocalHub session URL.
    """
    base_url = url.rstrip("/")
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = "http://" + base_url

    collaborator_name = name
    if not collaborator_name:
        collaborator_name = typer.prompt("Enter your collaborator name/identity")

    console.print(f"[cyan]Connecting to LocalHub session at[/cyan] [bold]{base_url}[/bold]...")

    http_session = requests.Session()

    # Step 1: Submit access request
    try:
        req_resp = http_session.post(f"{base_url}/login", data={"username": collaborator_name}, timeout=10)
        if req_resp.status_code == 410:
            console.print("[bold red]Error:[/bold red] The LocalHub session at this URL has been stopped.")
            raise typer.Exit(code=1)
        req_resp.raise_for_status()
    except Exception as e:
        console.print(f"[bold red]Connection error:[/bold red] Could not connect to LocalHub URL '{base_url}'. ({e})")
        raise typer.Exit(code=1)

    # Step 2: Poll status until approved or rejected
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        task = progress.add_task(description="Waiting for repository owner approval...", total=None)
        
        while True:
            time.sleep(2)
            try:
                status_resp = http_session.get(f"{base_url}/api/request-status", timeout=5)
                if status_resp.status_code == 410:
                    console.print("[bold red]Session stopped by repository owner.[/bold red]")
                    raise typer.Exit(code=1)
                
                status_data = status_resp.json()
                current_status = status_data.get("status")

                if current_status == "approved":
                    progress.update(task, description="Access approved! Preparing repository clone stream...")
                    break
                elif current_status == "rejected":
                    console.print("\n[bold red]❌ Access Request Rejected:[/bold red] The repository owner rejected your access request.")
                    raise typer.Exit(code=1)
            except Exception as e:
                console.print(f"\n[bold red]Error polling request status:[/bold red] {e}")
                raise typer.Exit(code=1)

    # Step 3: Fetch zip archive
    try:
        clone_resp = http_session.get(f"{base_url}/api/clone", stream=True, timeout=30)
        if clone_resp.status_code != 200:
            console.print(f"[bold red]Clone failed:[/bold red] Server returned status {clone_resp.status_code}")
            raise typer.Exit(code=1)

        # Parse filename from header or fallback
        cd_header = clone_resp.headers.get("Content-Disposition", "")
        repo_filename = "cloned_repo"
        if "filename=" in cd_header:
            repo_filename = cd_header.split("filename=")[-1].strip('"').replace(".zip", "")

        target_dir_name = destination or repo_filename
        target_dir = Path.cwd() / target_dir_name

        zip_bytes = io.BytesIO(clone_resp.content)
        with zipfile.ZipFile(zip_bytes, "r") as zip_ref:
            target_dir.mkdir(parents=True, exist_ok=True)
            zip_ref.extractall(target_dir)

        # Create local .localhub metadata
        localhub_meta_dir = target_dir / ".localhub"
        localhub_meta_dir.mkdir(exist_ok=True)
        meta_file = localhub_meta_dir / "config.json"
        
        import json
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump({
                "remote_url": base_url,
                "collaborator_name": collaborator_name,
                "cloned_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)

        console.print(Panel(
            f"[bold green]✓ Repository successfully cloned![/bold green]\n"
            f"[dim]Destination:[/dim] [bold white]{target_dir}[/bold white]\n"
            f"[dim]Remote URL:[/dim] [bold cyan]{base_url}[/bold cyan]",
            title="LocalHub Clone Complete",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"[bold red]Failed to download and extract repository:[/bold red] {e}")
        raise typer.Exit(code=1)


# ============================================================
# COMMAND: PUSH
# ============================================================

@app.command()
def push():
    """
    Synchronize local changes back to active LocalHub session (V3 synchronization foundation).
    """
    localhub_config = Path.cwd() / ".localhub" / "config.json"
    if not localhub_config.exists():
        console.print("[yellow]Warning:[/yellow] Not in a LocalHub cloned repository directory.")
        console.print("Run `localhub push` inside a repository cloned with `localhub clone <URL>`.")
        raise typer.Exit(code=1)

    try:
        import json
        with open(localhub_config, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        
        remote_url = cfg.get("remote_url")
        console.print(f"[cyan]Connecting to remote session at[/cyan] [bold]{remote_url}[/bold]...")

        resp = requests.post(f"{remote_url}/api/push", timeout=10)
        data = resp.json()

        console.print(Panel(
            f"[bold yellow]LocalHub Push Protocol V2/V3 Foundation[/bold yellow]\n"
            f"[white]{data.get('message', 'Push synchronization foundation active.')}[/white]\n\n"
            f"[dim]To prevent accidental overwrites, LocalHub requires repository owner approval for code pushes in V2.[/dim]",
            title="LocalHub Push Status",
            border_style="yellow"
        ))

    except Exception as e:
        console.print(f"[bold red]Push error:[/bold red] {e}")


# ============================================================
# COMMAND: VERSION
# ============================================================

@app.command()
def version():
    """
    Display LocalHub CLI version.
    """
    console.print(f"[bold cyan]LocalHub[/bold cyan] version [bold green]{VERSION}[/bold green]")


if __name__ == "__main__":
    app()