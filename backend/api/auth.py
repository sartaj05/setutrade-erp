import secrets
from datetime import timedelta
from functools import wraps
from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.http import JsonResponse
from django.utils import timezone
from .models import AuthSession

ACCESS_SALT = 'setustock.api.access'
REFRESH_SALT = 'setustock.api.refresh'


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')) or None


def create_session_tokens(user, request=None):
    token_id = secrets.token_urlsafe(24)
    expires_at = timezone.now() + timedelta(seconds=settings.AUTH_REFRESH_MAX_AGE)
    AuthSession.objects.create(
        user=user,
        token_id=token_id,
        expires_at=expires_at,
        user_agent=(request.headers.get('User-Agent', '')[:240] if request else ''),
        ip_address=_client_ip(request) if request else None,
    )
    base = {'uid': user.id, 'sid': token_id}
    access = signing.dumps(base, salt=ACCESS_SALT, compress=True)
    refresh = signing.dumps(base, salt=REFRESH_SALT, compress=True)
    return access, refresh


def create_token(user):
    """Backwards-compatible helper used by older code/tests."""
    access, _ = create_session_tokens(user)
    return access


def _load_payload(token, salt, max_age):
    return signing.loads(token, salt=salt, max_age=max_age)


def get_user_from_request(request):
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    token = header[7:].strip()
    try:
        payload = _load_payload(token, ACCESS_SALT, settings.AUTH_TOKEN_MAX_AGE)
        session = AuthSession.objects.select_related('user__profile__company', 'user__profile__branch').get(
            token_id=payload['sid'], user_id=payload['uid']
        )
        if not session.active:
            return None
        return session.user
    except (signing.BadSignature, signing.SignatureExpired, AuthSession.DoesNotExist, KeyError, User.DoesNotExist):
        return None


def refresh_access_token(refresh_token):
    try:
        payload = _load_payload(refresh_token, REFRESH_SALT, settings.AUTH_REFRESH_MAX_AGE)
        session = AuthSession.objects.select_related('user__profile__company', 'user__profile__branch').get(
            token_id=payload['sid'], user_id=payload['uid']
        )
        if not session.active or not session.user.is_active:
            return None, None
        access = signing.dumps({'uid': session.user_id, 'sid': session.token_id}, salt=ACCESS_SALT, compress=True)
        return access, session.user
    except (signing.BadSignature, signing.SignatureExpired, AuthSession.DoesNotExist, KeyError):
        return None, None


def revoke_request_session(request):
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return
    try:
        payload = _load_payload(header[7:].strip(), ACCESS_SALT, settings.AUTH_TOKEN_MAX_AGE)
        AuthSession.objects.filter(token_id=payload['sid'], revoked_at__isnull=True).update(revoked_at=timezone.now())
    except (signing.BadSignature, signing.SignatureExpired, KeyError):
        return


def api_auth_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        user = get_user_from_request(request)
        if not user:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        profile = getattr(user, 'profile', None)
        if not profile or not profile.company or not profile.company.is_active:
            return JsonResponse({'detail': 'Your account is not attached to an active company.'}, status=403)
        request.api_user = user
        request.company = profile.company
        request.branch = profile.branch
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
