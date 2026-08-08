import uuid


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

    return True


# ============================================================
# REJECT REQUEST
# ============================================================

def reject_request(request_id):

    request = access_requests.get(request_id)

    if not request:
        return False

    request["status"] = "rejected"

    return True


# ============================================================
# GET ALL PENDING REQUESTS
# ============================================================

def get_pending_requests():

    return [
        request
        for request in access_requests.values()
        if request["status"] == "pending"
    ]