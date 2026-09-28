import uuid
import logging
import time
from django.conf import settings
from django.http import HttpResponse

logger = logging.getLogger('setustock.request')


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        request.request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex
        try:
            response = self.get_response(request)
        except Exception:
            elapsed = round((time.perf_counter() - started) * 1000, 2)
            logger.exception('request_failed request_id=%s method=%s path=%s duration_ms=%s', request.request_id, request.method, request.path, elapsed)
            raise
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        response['X-Request-ID'] = request.request_id
        response['X-Response-Time-ms'] = str(elapsed)
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'camera=(self), microphone=(), geolocation=()'
        if response.status_code >= 500:
            logger.error('request_5xx request_id=%s method=%s path=%s status=%s duration_ms=%s', request.request_id, request.method, request.path, response.status_code, elapsed)
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
