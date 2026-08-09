import uuid
from datetime import datetime

# ============================================================
# ACCESS REQUEST STORAGE
# ============================================================

access_requests = {}


# ============================================================
# CREATE ACCESS REQUEST
# ============================================================

def create_request(username):
    request_id = str(uuid.uuid4())

    access_requests[request_id] = {
        "id": request_id,
        "username": username,
        "status": "pending",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return request_id


# ============================================================
# GET REQUEST
# ============================================================

def get_request(request_id):
    return access_requests.get(request_id)


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

def get_pending_requests():
    return [
        request
        for request in access_requests.values()
        if request["status"] == "pending"
    ]


# ============================================================
# GET APPROVED REQUESTS
# ============================================================

def get_approved_requests():
    return [
        request
        for request in access_requests.values()
        if request["status"] == "approved"
    ]


# ============================================================
# GET ALL REQUESTS
# ============================================================

def get_all_requests():
    return list(access_requests.values())


# ============================================================
# CLEAR ALL REQUESTS (FOR NEW SESSION)
# ============================================================

def clear_all_requests():
    access_requests.clear()