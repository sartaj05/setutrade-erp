import uuid
from django.conf import settings
from django.http import HttpResponse


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex
        response = self.get_response(request)
        response['X-Request-ID'] = request.request_id
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'camera=(self), microphone=(), geolocation=()'
        return response


class SimpleCorsMiddleware:
    """Dependency-free allow-list CORS middleware for the JSON API."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get('Origin', '').rstrip('/')
        if request.method == 'OPTIONS':
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        if origin and origin in settings.CORS_ALLOWED_ORIGINS:
            response['Access-Control-Allow-Origin'] = origin
            response['Vary'] = 'Origin'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-Request-ID'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Expose-Headers'] = 'X-Request-ID'
        return response
