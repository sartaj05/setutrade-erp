from functools import wraps
from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.http import JsonResponse

TOKEN_SALT = 'setustock.api.auth'

def create_token(user):
    role = getattr(getattr(user, 'profile', None), 'role', 'SALES')
    return signing.dumps({'uid': user.id, 'role': role}, salt=TOKEN_SALT, compress=True)

def get_user_from_request(request):
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    token = header[7:].strip()
    try:
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=settings.AUTH_TOKEN_MAX_AGE)
        return User.objects.select_related('profile').get(id=payload['uid'], is_active=True)
    except (signing.BadSignature, signing.SignatureExpired, User.DoesNotExist, KeyError):
        return None

def api_auth_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        request.api_user = user
        return view_func(request, *args, **kwargs)
    return wrapped

def roles_allowed(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @api_auth_required
        def wrapped(request, *args, **kwargs):
            if request.api_user.profile.role not in roles:
                return JsonResponse({'detail': 'You do not have access to this module.'}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
