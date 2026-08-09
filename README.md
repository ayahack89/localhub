# LocalHub 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](cli/main.py)

**Temporary local collaboration platform for developers.**  
*Instant local repository sharing with owner access control, automatic tunnel links, and snapshot cloning.*

---

## ⚡ What is LocalHub?

LocalHub is a lightweight, local-first alternative to third-party cloud hosting when you want to collaborate on a local project **right now**.

Instead of pushing private code to an external service or setting up complex cloud access:
1. Open your project folder in the terminal (`cd /path/to/my-app`)
2. Run **`localhub start`**
3. Share the temporary link with your collaborators
4. Approve access requests in real time from your owner dashboard
5. Collaborators browse your repository or run **`localhub clone <URL>`** to get a local copy

When you're finished, run **`localhub stop`** to terminate the session and disconnect all access.

---

## ⏱️ 30-Second Quick Start

```bash
# 1. Install LocalHub
pip install localhub

# 2. Open any project directory
cd ~/projects/demo-app

# 3. Start sharing your project
localhub start
```

### What happens when you run `localhub start`:
* Automatically detects the project directory as the active repository root.
* Launches the secure LocalHub server and Cloudflare public tunnel.
* Prints a rich terminal dashboard with your temporary share URL.
* Automatically opens your browser to the **Owner Command Center**.

---

## 🛠️ CLI Command Reference

| Command | Description |
| :--- | :--- |
| `localhub start [PATH]` | Start a temporary collaboration session for the current (or specified) directory. |
| `localhub stop` | Terminate the active LocalHub session and tunnel immediately. |
| `localhub status` | Display the status, active URLs, and metadata of the current session. |
| `localhub clone <URL>` | Request access and clone a snapshot of a shared LocalHub project locally. |
| `localhub push` | Foundation command for future V3 commit/snapshot synchronization. |
| `localhub version` | Display LocalHub CLI version (`0.2.0`). |

### CLI Options for `localhub start`
* `--port, -p INTEGER`: Port to run the local server on (default: `5000`).
* `--no-browser`: Disable automatic browser opening for the owner dashboard.

---

## 👥 Owner Workflow

1. Run `localhub start` in your project folder.
2. The **Owner Command Center** opens automatically at `http://127.0.0.1:5000/admin`.
3. Copy the generated **Temporary Share URL** (e.g. `https://xxxx.trycloudflare.com`).
4. Send the URL to your team members or collaborators.
5. As collaborators open the link and submit access requests, they appear in your dashboard in real time.
6. Click **Approve** to grant access, or **Reject** to deny it.
7. Click **Stop Session** when collaboration is complete.

---

## 💻 Collaborator Workflow

1. Open the share URL provided by the repository owner.
2. Enter your name or collaborator identity on the access request page.
3. Wait on the real-time approval screen (no manual refresh needed).
4. Once approved, browse the repository tree, view formatted code files, or download binary assets.
5. Alternatively, clone the project directly via CLI:
   ```bash
   localhub clone https://xxxx.trycloudflare.com
   ```
6. The CLI will request access, wait for approval, download the repository archive, extract the tree into `./<repo-name>`, and create a local `.localhub/config.json` configuration file.

---

## 🔒 Security & Privacy Model

* **Local-First Storage**: Your project files remain on your own machine. LocalHub serves files directly from your repository root without uploading your code to third-party databases.
* **Strict Path Traversal Guards**: Every file access request resolves paths relative to the active repository root and enforces strict path resolution checks. You cannot navigate outside the shared directory (`../` traversal is blocked).
* **Owner Access Control**: Collaborators cannot view any repository route or download any code until the repository owner explicitly approves their request ID.
* **Owner Dashboard Protection**: Dashboard control links (`/admin/*`) require authentication tokens or environment variable passwords (`LOCALHUB_ADMIN_PASSWORD`).
* **Hidden Files Isolation**: Internal LocalHub metadata (`.localhub`), `.git`, `.env`, and virtual environments (`venv`) are automatically filtered from browser file listings.
* **Instant Session Revocation**: When `localhub stop` is executed, the server and tunnel shut down, rendering the temporary URL completely inactive.

For more security information, please refer to [SECURITY.md](SECURITY.md).

---

## ⚙️ Environment Configuration

LocalHub supports environment variables for securing dashboard access and configuring session options.

Copy the provided template to create your local `.env` file:
```bash
cp .env.example .env
```

> **Note**: `.env` is automatically ignored by `.gitignore` to prevent leaking sensitive credentials. Never commit `.env` to version control.

---

## 🏗️ Architecture Overview

LocalHub V2 is structured into clean modular layers:

* **CLI Module (`cli/main.py`)**: Built with Typer and Rich to provide a sleek terminal command interface.
* **Session Manager (`Backend/services/session.py`)**: Manages live session metadata, session IDs, owner tokens, activity logs, and `.localhub/session.json`.
* **Repository Service (`Backend/services/repository.py`)**: Resolves directory trees dynamically per session and enforces security boundaries.
* **Access Service (`Backend/services/access.py`)**: Manages access request states (`pending`, `approved`, `rejected`).
* **Tunnel Service (`Backend/services/tunnel.py`)**: Integrates Cloudflare tunnels dynamically for temporary URL generation.
* **Flask Web Server (`Backend/app.py`)**: Clean REST & SSR endpoints with modern dark-mode Jinja2 templates.

---

## 💻 Development & Open Source Setup

We welcome contributions! To set up LocalHub for local development:

```bash
# 1. Clone repository
git clone https://github.com/ayahack89/localhub.git
cd localhub

# 2. Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies in editable mode
pip install -e .

# 4. Run test suite
python -m unittest discover tests
```

---

## 🤝 Community & Contributing

* Read our [CONTRIBUTING.md](CONTRIBUTING.md) guide for guidelines on submitting issues and pull requests.
* Follow our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) to maintain a respectful and welcoming environment.
* Report security vulnerabilities responsibly as outlined in [SECURITY.md](SECURITY.md).

---

## 📌 Roadmap

- [x] **V2.0 Core Release**: Real Global CLI (`localhub start`), dynamic directory detection, owner auto-login dashboard, real-time access request approval/rejection polling, GitHub-inspired dark developer UI, and `localhub clone <URL>` snapshot cloning.
- [ ] **V3.0 Commit & Sync Layer**: Change-set tracking, diff preview before applying collaborator changes, and bi-directional `localhub push` / `localhub pull`.
- [ ] **Granular File Permissions**: Read-only vs. write permissions per collaborator.

---

## 📄 License

LocalHub is open-source software licensed under the [MIT License](LICENSE).
