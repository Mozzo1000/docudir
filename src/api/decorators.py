from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from flask import jsonify
from functools import wraps
import sys
import inspect
from api.models import User, Site

def check_site_permissions(site_id):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if (site_id in kwargs):
                print(kwargs[site_id])
                verify_jwt_in_request()
                current_user = User.find_by_email(get_jwt_identity())
                site = Site.query.filter(Site.id==kwargs[site_id], Site.members.any(id=current_user.id)).first()
                if site:
                    return fn(*args, **kwargs)
                else:
                    return jsonify({
                        "error": "Not found",
                        "message": "Site not found"
                    }), 404
            else:
                return jsonify({
                    "error": "Unknown error",
                    "message": "Unkown error occurred"
                }), 500
        return decorator
    return wrapper