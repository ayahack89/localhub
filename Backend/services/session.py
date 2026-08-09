import os
import json
import uuid
from pathlib import Path
from datetime import datetime

_ACTIVE_SESSION = {
    "session_id": None,
    "repo_name": "",
    "repo_path": "",
    "status": "STOPPED",
    "start_time": None,
    "local_url": "http://127.0.0.1:5000",
    "public_url": None,
    "admin_token": None,
    "activities": []
}

class SessionService:

    @classmethod
    def init_session(cls, repo_path, port=5000, admin_token=None):
        repo_path_obj = Path(repo_path).resolve()
        
        token = admin_token or os.urandom(16).hex()
        session_id = str(uuid.uuid4())
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        _ACTIVE_SESSION["session_id"] = session_id
        _ACTIVE_SESSION["repo_name"] = repo_path_obj.name
        _ACTIVE_SESSION["repo_path"] = str(repo_path_obj)
        _ACTIVE_SESSION["status"] = "LIVE"
        _ACTIVE_SESSION["start_time"] = now_str
        _ACTIVE_SESSION["local_url"] = f"http://127.0.0.1:{port}"
        _ACTIVE_SESSION["public_url"] = None
        _ACTIVE_SESSION["admin_token"] = token
        _ACTIVE_SESSION["port"] = port
        _ACTIVE_SESSION["activities"] = [
            {"time": datetime.now().strftime("%H:%M:%S"), "message": f"Session initialized for '{repo_path_obj.name}'"}
        ]

        cls._save_session_file(repo_path_obj)
        return _ACTIVE_SESSION

    @classmethod
    def set_public_url(cls, public_url):
        _ACTIVE_SESSION["public_url"] = public_url
        cls.log_activity(f"Public URL active: {public_url}")
        if _ACTIVE_SESSION["repo_path"]:
            cls._save_session_file(Path(_ACTIVE_SESSION["repo_path"]))

    @classmethod
    def get_session(cls):
        # If active session memory is empty, attempt reading from .localhub/session.json in cwd
        if not _ACTIVE_SESSION["session_id"]:
            cls._load_session_file(Path.cwd())
        return _ACTIVE_SESSION

    @classmethod
    def is_live(cls):
        session = cls.get_session()
        return session.get("status") == "LIVE"

    @classmethod
    def log_activity(cls, message):
        activity = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": message
        }
        _ACTIVE_SESSION["activities"].insert(0, activity)
        # Keep last 50 activities
        _ACTIVE_SESSION["activities"] = _ACTIVE_SESSION["activities"][:50]

    @classmethod
    def stop_session(cls):
        _ACTIVE_SESSION["status"] = "STOPPED"
        cls.log_activity("Session stopped by repository owner")
        if _ACTIVE_SESSION["repo_path"]:
            cls._save_session_file(Path(_ACTIVE_SESSION["repo_path"]))

    @classmethod
    def _save_session_file(cls, repo_path_obj):
        try:
            localhub_dir = repo_path_obj / ".localhub"
            localhub_dir.mkdir(exist_ok=True)
            session_file = localhub_dir / "session.json"
            
            data_to_save = {k: v for k, v in _ACTIVE_SESSION.items() if k != "admin_token"}
            data_to_save["admin_token_hash"] = hash(_ACTIVE_SESSION["admin_token"]) if _ACTIVE_SESSION["admin_token"] else None
            
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save .localhub/session.json: {e}")

    @classmethod
    def _load_session_file(cls, repo_path_obj):
        session_file = repo_path_obj / ".localhub" / "session.json"
        if session_file.exists():
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if k in _ACTIVE_SESSION:
                            _ACTIVE_SESSION[k] = v
            except Exception:
                pass
