import os
import uuid
from datetime import datetime

# ============================================================
# ACCESS REQUEST STORAGE
# ============================================================

access_requests = {}


# ============================================================
# CREATE ACCESS REQUEST
# ============================================================

def create_request(username, session_id=None):
    request_id = str(uuid.uuid4())
    token = os.urandom(16).hex()

    access_requests[request_id] = {
        "id": request_id,
        "token": token,
        "username": username,
        "status": "pending",
        "session_id": session_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return request_id


# ============================================================
# GET REQUEST
# ============================================================

def get_request(request_id):
    return access_requests.get(request_id)


# ============================================================
# GET REQUEST BY TOKEN OR ID
# ============================================================

def get_request_by_token(token):
    if not token:
        return None
    for req in access_requests.values():
        if req.get("token") == token or req.get("id") == token:
            return req
    return None


# ============================================================
# APPROVE REQUEST
# ============================================================

def approve_request(request_id):
    request = access_requests.get(request_id)

    if not request:
        return False

    request["status"] = "approved"
    request["approved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return True


# ============================================================
# REJECT REQUEST
# ============================================================

def reject_request(request_id):
    request = access_requests.get(request_id)

    if not request:
        return False

    request["status"] = "rejected"
    request["rejected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return True


# ============================================================
# GET PENDING REQUESTS
# ============================================================

def get_pending_requests(session_id=None):
    return [
        request
        for request in access_requests.values()
        if request["status"] == "pending" and (session_id is None or request.get("session_id") == session_id)
    ]


# ============================================================
# GET APPROVED REQUESTS
# ============================================================

def get_approved_requests(session_id=None):
    return [
        request
        for request in access_requests.values()
        if request["status"] == "approved" and (session_id is None or request.get("session_id") == session_id)
    ]


# ============================================================
# GET ALL REQUESTS
# ============================================================

def get_all_requests(session_id=None):
    if session_id is None:
        return list(access_requests.values())
    return [req for req in access_requests.values() if req.get("session_id") == session_id]


# ============================================================
# CLEAR ALL REQUESTS (FOR NEW SESSION)
# ============================================================

def clear_all_requests():
    access_requests.clear()