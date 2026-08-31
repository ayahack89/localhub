# LocalHub 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](pyproject.toml)
[![Build Status](https://img.shields.io/badge/tests-30%20passed-brightgreen.svg)](tests/)

**A local-first collaboration platform and CLI engine for developers.**  
*Instant local repository sharing with owner access control, automatic tunnel links, and snapshot cloning.*

> **Release Version**: `v2.0.0` (Major release following `v1.0.0`)

---

## 📖 Table of Contents

- [Section A: Developer Guide](#-section-a-developer-guide)
  - [What is LocalHub?](#what-is-localhub)
  - [Why LocalHub Exists & Key Benefits](#why-localhub-exists--key-benefits)
  - [Architecture & Technology Overview](#architecture--technology-overview)
  - [Development Setup](#development-setup)
  - [Running Tests](#running-tests)
  - [Contribution Information](#contribution-information)
  - [Security Information](#security-information)
- [Section B: User & Collaborator Guide](#-section-b-user--collaborator-guide)
  - [Installation](#installation)
  - [30-Second Quick Start](#30-second-quick-start)
  - [Owner Workflow](#owner-workflow)
  - [Collaborator Workflow](#collaborator-workflow)
  - [Browsing & Snapshot Cloning](#browsing--snapshot-cloning)
  - [CLI Command Reference](#cli-command-reference)
  - [Stopping a Session](#stopping-a-session)
  - [Security & Privacy Overview](#security--privacy-overview)
- [License](#-license)

---

# 🛠️ Section A: Developer Guide

### What is LocalHub?

LocalHub is a lightweight, local-first developer tool that enables instant, peer-to-peer code collaboration directly from your machine. Instead of pushing incomplete or sensitive code to third-party cloud git providers, LocalHub runs a temporary local server on your machine, generates a secure public tunnel URL via Cloudflare (or serves locally), and provides both a browser UI and a CLI for collaborators to review, browse, and clone your project.

### Why LocalHub Exists & Key Benefits

Traditional code collaboration requires creating remote git repositories, configuring organizational permissions, or copying code archives to external cloud storage. LocalHub solves this with:

* **Zero-Cloud Dependency**: Source code is streamed directly from your local filesystem. No third-party servers store your repository.
* **Owner-Controlled Access**: Collaborators cannot browse files or download code until you explicitly approve their request from your Owner Command Center.
* **Instant Snapshot Cloning**: Collaborators can clone your exact repository state using `localhub clone <URL>` without setting up remote git origins.
* **Automated Tunneling**: Integrates seamlessly with Cloudflare tunnels to make local servers accessible worldwide without manual port forwarding.
* **Strict Boundary Isolation**: Built-in security filters automatically shield `.env`, `.git`, `.localhub`, and virtual environment directories from directory browsing and archives.

---

### Architecture & Technology Overview

LocalHub is built with a modular, service-oriented architecture:

```
┌────────────────────────────────────────────────────────┐
│                      LocalHub CLI                      │
│        (Typer, Rich, Click, Packaging metadata)        │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
                ▼                        ▼
┌───────────────────────────────┐ ┌──────────────────────┐
│       Session Service         │ │    Tunnel Service    │
│  Session metadata, Activity   │ │   Cloudflare Tunnel  │
│  logs, .localhub/session.json │ │      Subprocess      │
└───────────────┬───────────────┘ └──────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────┐
│                   Flask Web Engine                     │
│  • Web UI (Jinja2, Deep-Dark Developer Design System)  │
│  • REST APIs (/api/request-status, /api/clone, etc.)   │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
                ▼                        ▼
┌───────────────────────────────┐ ┌──────────────────────┐
│      Repository Service       │ │    Access Service    │
│ Directory traversal guards,   │ │  In-memory request   │
│ path resolution, file streams │ │    state lifecycle   │
└───────────────────────────────┘ └──────────────────────┘
```

#### Core Components:
* **CLI Layer (`cli/main.py`)**: Built on Typer and Rich. Handles terminal commands (`start`, `stop`, `status`, `clone`, `push`, `version`) and displays formatted terminal dashboards.
* **Web Server (`Backend/app.py`)**: Flask web application providing server-side rendered pages for repository browsing, file viewing, access request submission, and the Owner Command Center.
* **Session Manager (`Backend/services/session.py`)**: Manages session state (`LIVE` / `STOPPED`), port configurations, activity feeds, and saves session metadata to `.localhub/session.json`.
* **Repository Service (`Backend/services/repository.py`)**: Resolves directory structures dynamically, ensures file access never escapes the repository root (`is_relative_to` boundary validation), and filters protected files.
* **Access Controller (`Backend/services/access.py`)**: Manages access request lifecycles (`pending`, `approved`, `rejected`) and generates cryptographic session tokens.
* **Tunnel Manager (`Backend/services/tunnel.py`)**: Spawns and manages Cloudflare tunnel processes for secure external access.

---

### Development Setup

To set up LocalHub locally for development:

```bash
# 1. Clone the repository
git clone https://github.com/ayahack89/localhub.git
cd localhub

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install the package in editable mode
pip install -e .

# 4. Verify installation
localhub version
```

---

### Running Tests

LocalHub includes a comprehensive unit and integration test suite covering CLI commands, security boundaries, authentication, and live cloning flows:

```bash
# Run unit test discovery
python -m unittest discover tests

# Run live end-to-end integration test
python tests/test_live_cli.py
```

---

### Contribution Information

Contributions, bug reports, and suggestions are welcome!

1. Fork the repository and create a feature branch (`git checkout -b feature/my-feature`).
2. Ensure all changes adhere to existing coding style and pass the complete test suite.
3. Submit a pull request detailing your changes.

Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for full community guidelines.

---

### Security Information

LocalHub incorporates multiple defensive layers to protect local source code and secrets:

* **Path Traversal Defense**: All file requests are validated to ensure absolute paths resolve inside the repository root. Traversal attempts (e.g. `../../etc/passwd`) are rejected with `403 Forbidden`.
* **Sensitive File Shielding**: Files and directories matching `.env*`, `.git`, `.localhub`, `venv`, `.venv`, and `__pycache__` are excluded from file listings and snapshot archives.
* **Owner Authentication**: Sensitive management routes (`/admin/*`) require a valid session token or `LOCALHUB_ADMIN_PASSWORD`.
* **Session Ephemerality**: Stopping a session immediately terminates server routes and public tunnels, returning `410 Gone` to all subsequent collaborator requests.

To report security issues privately, see [SECURITY.md](SECURITY.md).

---

# 👥 Section B: User & Collaborator Guide

### Installation

Install LocalHub via pip:

```bash
pip install localhub
```

Requirements: Python 3.9+ and optionally [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) for public tunneling.

---

### 30-Second Quick Start

```bash
# 1. Navigate to your project directory
cd ~/projects/my-app

# 2. Start sharing
localhub start
```

When you run `localhub start`:
1. LocalHub initializes the current directory as the active repository root.
2. A local server and public Cloudflare tunnel are launched.
3. A terminal dashboard displays your **Share URL** and **Owner Dashboard** URL.
4. Your default browser automatically opens the **Owner Command Center**.

---

### Owner Workflow

```
[Start Session] ──> [Share URL with Team] ──> [Review Access Requests] ──> [Approve / Reject] ──> [Stop Session]
```

1. **Launch**: Run `localhub start` in your project folder.
2. **Share**: Copy the generated **Share URL** (e.g. `https://xxxx.trycloudflare.com`) or local LAN address.
3. **Manage**: Open the Owner Command Center at `http://127.0.0.1:5000/admin`.
4. **Approve**: As team members connect, their requests appear in real time. Click **Approve** to grant read and clone access, or **Reject** to decline.
5. **Monitor**: View live session statistics, approved collaborator lists, and activity logs.
6. **Terminate**: Click **Stop Session** in the UI or press `Ctrl+C` in your terminal to close the session.

---

### Collaborator Workflow

1. Open the **Share URL** sent by the repository owner in your web browser.
2. Enter your name or developer identity on the **Request Access** page.
3. Wait on the approval screen (the interface automatically updates when the owner approves your request).
4. Once approved, explore the repository files in the browser or clone the snapshot locally.

---

### Browsing & Snapshot Cloning

#### In-Browser Explorer
* **Directory Navigation**: Browse repository hierarchy with folder and file Octicons.
* **Code Viewer**: View formatted source files with syntax styling and one-click "Copy Code".
* **Raw Downloads**: Download individual binary assets or source files.

#### CLI Snapshot Clone
Approved collaborators can clone the repository snapshot directly into a local folder:

```bash
# Interactive clone (prompts for collaborator identity):
localhub clone https://xxxx.trycloudflare.com

# Direct clone with specified collaborator name and destination:
localhub clone https://xxxx.trycloudflare.com --name "Alex" --out my-local-copy
```

The CLI requests access, monitors approval status, downloads the archive, extracts it into the target directory, and saves session metadata to `.localhub/config.json`.

---

### CLI Command Reference

| Command | Description | Options |
| :--- | :--- | :--- |
| `localhub start [PATH]` | Start a collaboration session for the specified (or current) directory. | `--port, -p INTEGER`<br>`--no-browser` |
| `localhub stop` | Terminate the active LocalHub session and public tunnel. | None |
| `localhub status` | Display the status, active URLs, and metadata of the current session. | None |
| `localhub clone <URL>` | Request access and clone a snapshot of a shared LocalHub project. | `--name, -n TEXT`<br>`--out, -o TEXT`<br>`--token, -t TEXT` |
| `localhub push` | Verify synchronization connection with the remote LocalHub session. | None |
| `localhub version` | Display LocalHub CLI version (`2.0.0`). | `--version, -v` |

---

### Stopping a Session

To end collaboration and disconnect all access:

* **From CLI**: Run `localhub stop` or press `Ctrl+C` in the terminal running the session.
* **From Browser**: Click **Stop Session** in the top navigation bar of the Owner Command Center.

Once stopped, the public tunnel is killed, local routes return `410 Gone`, and all active collaborator sessions are terminated immediately.

---

### Security & Privacy Overview

* **Your Code Stays on Your Machine**: Files are streamed directly from your device on demand.
* **No Unauthenticated Access**: Unapproved visitors cannot view file paths, file contents, or download archives.
* **Private Metadata Protection**: `.env` credential files, `.git` history, and local virtual environments are never exposed.
* **Instant Revocation**: Stopping a session immediately terminates all incoming connections.

---

## 📄 License

LocalHub is open-source software licensed under the [MIT License](LICENSE).
