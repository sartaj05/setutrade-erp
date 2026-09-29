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

PLAN_ALIASES = {'FREE': 'FREE', 'STARTER': 'FREE', 'PREMIUM': 'PREMIUM', 'GROWTH': 'PREMIUM', 'ENTERPRISE': 'ENTERPRISE', 'BUSINESS': 'ENTERPRISE'}
PLAN_LABELS = {'FREE': 'Free', 'PREMIUM': 'Premium', 'ENTERPRISE': 'Enterprise'}
PLAN_LEVELS = {'FREE': 0, 'PREMIUM': 1, 'ENTERPRISE': 2}
PLAN_LIMITS = {'FREE': {'users': 3, 'products': 100, 'branches': 1, 'warehouses': 1, 'orders': 100}, 'PREMIUM': {'users': 10, 'products': 2500, 'branches': 3, 'warehouses': 5, 'orders': 1000}, 'ENTERPRISE': {'users': 50, 'products': 10000, 'branches': 20, 'warehouses': 50, 'orders': 10000}}
PLAN_FEATURES = {
    'FREE': {'whatsapp': False, 'tax': False, 'pricing': False, 'invoices': False, 'payments': False, 'delivery': False, 'approvals': False, 'field-sales': False, 'collections': False, 'offline': False, 'forecasting': False, 'assistant': False, 'traceability': False, 'wms': False, 'invoice-ocr': False, 'accounting': False, 'gst-cockpit': False, 'procurement-intelligence': False, 'fleet-routes': False, 'product-master': False, 'service-rma': False, 'quality': False, 'supply-planning': False, 'distribution-network': False, 'credit-risk': False, 'security-center': False, 'integrations': False, 'executive-bi': False, 'copilot-actions': False, 'treasury': False, 'contracts': False, 'expenses': False, 'report-builder': False, 'operations-center': False, 'team': False, 'audit': False},
    'PREMIUM': {'whatsapp': True, 'tax': True, 'pricing': True, 'invoices': True, 'payments': True, 'delivery': True, 'approvals': True, 'field-sales': True, 'collections': True, 'offline': True, 'forecasting': True, 'assistant': True, 'traceability': True, 'wms': True, 'invoice-ocr': True, 'accounting': True, 'gst-cockpit': True, 'procurement-intelligence': True, 'fleet-routes': True, 'product-master': True, 'service-rma': True, 'quality': True, 'supply-planning': True, 'distribution-network': False, 'credit-risk': False, 'security-center': False, 'integrations': False, 'executive-bi': False, 'copilot-actions': False, 'treasury': False, 'contracts': False, 'expenses': False, 'report-builder': False, 'operations-center': False, 'team': False, 'audit': False},
    'ENTERPRISE': {'whatsapp': True, 'tax': True, 'pricing': True, 'invoices': True, 'payments': True, 'delivery': True, 'approvals': True, 'field-sales': True, 'collections': True, 'offline': True, 'forecasting': True, 'assistant': True, 'traceability': True, 'wms': True, 'invoice-ocr': True, 'accounting': True, 'gst-cockpit': True, 'procurement-intelligence': True, 'fleet-routes': True, 'product-master': True, 'service-rma': True, 'quality': True, 'supply-planning': True, 'distribution-network': True, 'credit-risk': True, 'security-center': True, 'integrations': True, 'executive-bi': True, 'copilot-actions': True, 'treasury': True, 'contracts': True, 'expenses': True, 'report-builder': True, 'operations-center': True, 'team': True, 'audit': True},
}
for _plan_features in PLAN_FEATURES.values():
    _plan_features.setdefault('settings', False)
PLAN_FEATURES['ENTERPRISE']['settings'] = True

def normalize_plan_code(code):
    return PLAN_ALIASES.get(str(code or 'FREE').upper(), 'FREE')


def _subscription_snapshot(company):
    from .models import CompanySubscription
    today = timezone.localdate()
    subscription = CompanySubscription.objects.filter(company=company).select_related('plan').first()
    if not subscription:
        code = 'FREE'
        status = 'Trial'
        period_end = None
        trial_end = None
        limits = dict(PLAN_LIMITS[code])
    else:
        code = normalize_plan_code(subscription.plan.code)
        status = subscription.status
        if subscription.current_period_end and subscription.current_period_end < today:
            status = 'Expired' if subscription.status == 'Trial' else 'Past Due'
        period_end = subscription.current_period_end
        trial_end = subscription.trial_end
        limits = {key: getattr(subscription.plan, f'{key[:-1]}_limit' if key in ('users', 'branches', 'warehouses') else f'{key[:-1]}_limit' if key == 'products' else 'order_limit', default) for key, default in PLAN_LIMITS[code].items()}
    features = PLAN_FEATURES[code]
    return {'subscription': subscription, 'code': code, 'name': PLAN_LABELS[code], 'status': status, 'periodEnd': period_end, 'trialEnd': trial_end, 'limits': limits, 'features': features}


def subscription_usage(company):
    from django.contrib.auth.models import User
    from .models import Branch, Order, Product, Warehouse
    today = timezone.localdate()
    return {'users': User.objects.filter(profile__company=company, is_active=True).count(), 'products': Product.objects.filter(company=company, is_active=True).count(), 'branches': Branch.objects.filter(company=company, is_active=True).count(), 'warehouses': Warehouse.objects.filter(company=company, is_active=True).count(), 'orders': Order.objects.filter(company=company, order_date__year=today.year, order_date__month=today.month).count()}


def subscription_payload(company):
    snapshot = _subscription_snapshot(company)
    usage = subscription_usage(company)
    return {'code': snapshot['code'], 'name': snapshot['name'], 'status': snapshot['status'], 'periodEnd': snapshot['periodEnd'].isoformat() if snapshot['periodEnd'] else None, 'trialEnd': snapshot['trialEnd'].isoformat() if snapshot['trialEnd'] else None, 'daysRemaining': max(0, (snapshot['periodEnd'] - timezone.localdate()).days) if snapshot['periodEnd'] else None, 'limits': snapshot['limits'], 'userLimit': snapshot['limits']['users'], 'productLimit': snapshot['limits']['products'], 'branchLimit': snapshot['limits']['branches'], 'warehouseLimit': snapshot['limits']['warehouses'], 'orderLimit': snapshot['limits']['orders'], 'usage': usage, 'features': [key for key, enabled in snapshot['features'].items() if enabled], 'featureAccess': snapshot['features']}


def subscription_feature_for_path(request):
    path = request.path.split('/api/', 1)[-1].strip('/')
    module = path.split('/', 1)[0]
    return module if module in PLAN_FEATURES['FREE'] else None


def subscription_denial(request, feature):
    snapshot = _subscription_snapshot(request.company)
    required = 'ENTERPRISE' if not PLAN_FEATURES['PREMIUM'].get(feature, False) else 'PREMIUM'
    return JsonResponse({'detail': f'{feature.replace("-", " ").title()} requires the {PLAN_LABELS[required]} plan.', 'error': 'subscription_required', 'feature': feature, 'requiredPlan': required, 'currentPlan': snapshot['code'], 'status': snapshot['status'], 'upgradeUrl': '/app?module=subscription'}, status=402)


def subscription_allows(company, feature):
    snapshot = _subscription_snapshot(company)
    if snapshot['status'] in ('Expired', 'Past Due', 'Cancelled'):
        return False
    return bool(snapshot['features'].get(feature, False))


def usage_limit_response(request, resource, increment=1):
    snapshot = _subscription_snapshot(request.company)
    usage = subscription_usage(request.company)
    limit = snapshot['limits'].get(resource)
    if limit is not None and usage.get(resource, 0) + increment > limit:
        return JsonResponse({'detail': f'{resource.title()} limit reached for the {snapshot["name"]} plan.', 'error': 'subscription_limit_reached', 'resource': resource, 'limit': limit, 'usage': usage.get(resource, 0), 'currentPlan': snapshot['code'], 'requiredPlan': 'PREMIUM' if snapshot['code'] == 'FREE' else 'ENTERPRISE', 'upgradeUrl': '/app?module=subscription'}, status=402)
    return None


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
        feature = subscription_feature_for_path(request)
        if feature and not subscription_allows(request.company, feature):
            return subscription_denial(request, feature)
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

PORTAL_SALT = 'setustock.portal.access'

def create_portal_token(access):
    return signing.dumps({'aid': access.id, 'cid': access.customer_id, 'co': access.company_id}, salt=PORTAL_SALT, compress=True)

def portal_auth_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        from .models import CustomerPortalAccess
        header = request.headers.get('Authorization', '')
        if not header.startswith('Portal '):
            return JsonResponse({'detail': 'Customer portal authentication required.'}, status=401)
        try:
            payload = signing.loads(header[7:].strip(), salt=PORTAL_SALT, max_age=60 * 60 * 24 * 30)
            access = CustomerPortalAccess.objects.select_related('customer', 'company').get(pk=payload['aid'], is_active=True)
        except (signing.BadSignature, signing.SignatureExpired, CustomerPortalAccess.DoesNotExist, KeyError):
            return JsonResponse({'detail': 'Portal session is invalid or expired.'}, status=401)
        request.portal_access = access
        request.customer = access.customer
        request.company = access.company
        return view_func(request, *args, **kwargs)
    return wrapped
