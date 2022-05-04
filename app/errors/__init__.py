from flask import Blueprint

errors = Blueprint('errors', __name__)


@errors.errorhandler(400)
def bad_request(e):
    return {"error": {"message": e.description['message'], "code": 400}}, 400


@errors.errorhandler(401)
def unauthorized(_e):
    return {"error": {"message": "Unauthorized", "code": 401}}, 401


@errors.errorhandler(404)
def not_found(e):
    return {"error": {"message": e.description['message'], "code": 404}}, 404


@errors.errorhandler(429)
def too_many_requests(_e):
    return {"error": {"message": "Too many requests", "code": 429}}, 429


@errors.errorhandler(503)
def service_unavailable(_e):
    return {"error": {"message": "Service Unavailable", "code": 503}}, 503
