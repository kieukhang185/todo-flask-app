from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from flask import abort
from ..extensions import mongo


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        username = get_jwt_identity()
        user = mongo.db.users.find_one({'username': username})
        if not user or user.get('role') != 'admin':
            abort(403, 'Admin privilege required')
        return fn(*args, **kwargs)
    return wrapper