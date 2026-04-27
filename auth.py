from flask import request, jsonify, session
from functools import wraps


def get_current_user():
    user_id = session.get("user_id") or request.headers.get("user_id")
    role = session.get("role") or request.headers.get("role")
    return user_id, role


def require_role(required_roles):
    user_id, role = get_current_user()
    if not user_id or not role:
        return jsonify({"status": "error", "message": "Authentication required"}), 401
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    if role not in required_roles:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    return None


def require_role_decorator(required_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_response = require_role(required_roles)
            if error_response:
                return error_response
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_customer():
    return require_role("customer")


def require_staff_or_admin():
    return require_role(["staff", "admin"])


def require_admin():
    return require_role("admin")
