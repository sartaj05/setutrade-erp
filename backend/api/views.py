import json
from decimal import Decimal
from django.contrib.auth import authenticate
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from .auth import api_auth_required, create_token, roles_allowed
from .models import Customer, Invoice, Order, Product

PERMISSIONS = {
    'OWNER': ['dashboard','products','inventory','customers','orders','invoices','quotations','payments','reports','team','settings'],
    'MANAGER': ['dashboard','products','inventory','customers','orders','invoices','quotations','payments','reports'],
    'SALES': ['dashboard','customers','orders','invoices','quotations','payments'],
    'WAREHOUSE': ['dashboard','products','inventory','orders'],
    'ACCOUNTANT': ['dashboard','customers','orders','invoices','payments','reports'],
}

def user_payload(user):
    profile = user.profile
    display_name = user.get_full_name() or user.username
    return {
        'id': user.id,
        'name': display_name,
        'email': user.email,
        'role': profile.role,
        'business': profile.business_name,
        'permissions': PERMISSIONS.get(profile.role, []),
    }

@require_GET
def health(request):
    return JsonResponse({'ok': True, 'service': 'setustock-api'})

@csrf_exempt
@require_POST
def login_view(request):
    try:
        body = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid JSON.'}, status=400)
    email = str(body.get('email', '')).strip().lower()
    password = str(body.get('password', ''))
    if not email or not password:
        return JsonResponse({'detail': 'Email and password are required.'}, status=400)
    from django.contrib.auth.models import User
    account = User.objects.filter(email__iexact=email, is_active=True).first()
    if not account:
        return JsonResponse({'detail': 'Invalid email or password.'}, status=401)
    user = authenticate(request, username=account.username, password=password)
    if not user:
        return JsonResponse({'detail': 'Invalid email or password.'}, status=401)
    return JsonResponse({'token': create_token(user), 'user': user_payload(user)})

@require_GET
@api_auth_required
def me(request):
    return JsonResponse({'user': user_payload(request.api_user)})

@require_GET
@api_auth_required
def dashboard(request):
    today = timezone.localdate()
    sales_today = Order.objects.filter(order_date=today).aggregate(total=Sum('total'))['total'] or Decimal('0')
    receivable = Customer.objects.aggregate(total=Sum('outstanding'))['total'] or Decimal('0')
    low_stock = sum(1 for p in Product.objects.all() if p.stock <= p.reorder_level)
    stock_value = sum((p.stock * p.purchase_price for p in Product.objects.all()), Decimal('0'))
    recent = Order.objects.select_related('customer').order_by('-order_date', '-id')[:8]
    return JsonResponse({
        'metrics': {
            'salesToday': float(sales_today),
            'receivable': float(receivable),
            'stockValue': float(stock_value),
            'openOrders': Order.objects.exclude(status=Order.Status.DISPATCHED).count(),
            'lowStock': low_stock,
        },
        'recentOrders': [{
            'id': o.order_no, 'customer': o.customer.name, 'total': float(o.total),
            'status': o.status, 'payment': o.payment_status, 'date': o.order_date.strftime('%d %b')
        } for o in recent],
    })

@require_GET
@roles_allowed('OWNER', 'MANAGER', 'WAREHOUSE')
def products(request):
    rows = Product.objects.filter(is_active=True).order_by('name')
    return JsonResponse({'products': [{
        'sku': p.sku, 'name': p.name, 'category': p.category, 'stock': float(p.stock), 'unit': p.unit,
        'buy': float(p.purchase_price), 'sell': float(p.sell_price), 'reorder': float(p.reorder_level), 'location': p.location
    } for p in rows]})

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@roles_allowed('OWNER', 'MANAGER', 'SALES', 'ACCOUNTANT')
def customers(request):
    if request.method == 'POST':
        try: body = json.loads(request.body or '{}')
        except json.JSONDecodeError: return JsonResponse({'detail': 'Invalid JSON.'}, status=400)
        required = ['code', 'name']
        if any(not body.get(k) for k in required): return JsonResponse({'detail': 'code and name are required.'}, status=400)
        customer = Customer.objects.create(code=body['code'], name=body['name'], city=body.get('city',''), phone=body.get('phone',''), credit_limit=body.get('credit_limit',0))
        return JsonResponse({'id': customer.id, 'code': customer.code}, status=201)
    rows = Customer.objects.order_by('name')
    return JsonResponse({'customers': [{
        'id': c.code, 'name': c.name, 'city': c.city, 'phone': c.phone,
        'outstanding': float(c.outstanding), 'limit': float(c.credit_limit),
        'due': c.due_date.strftime('%d %b') if c.due_date else '—',
        'status': 'Overdue' if c.outstanding and c.due_date and c.due_date < timezone.localdate() else ('Current' if c.outstanding else 'Clear')
    } for c in rows]})

@require_GET
@roles_allowed('OWNER', 'MANAGER', 'SALES', 'WAREHOUSE', 'ACCOUNTANT')
def orders(request):
    rows = Order.objects.select_related('customer').order_by('-order_date', '-id')
    return JsonResponse({'orders': [{
        'id': o.order_no, 'customer': o.customer.name, 'total': float(o.total), 'status': o.status,
        'payment': o.payment_status, 'date': o.order_date.strftime('%d %b')
    } for o in rows]})


@require_GET
@roles_allowed('OWNER', 'MANAGER', 'SALES', 'ACCOUNTANT')
def invoices(request):
    rows = Invoice.objects.select_related('order__customer').order_by('-invoice_date', '-id')
    return JsonResponse({'invoices': [{
        'id': i.invoice_no, 'order': i.order.order_no, 'customer': i.order.customer.name, 'gstin': i.gstin,
        'taxable': float(i.taxable_amount), 'tax': float(i.cgst + i.sgst + i.igst), 'total': float(i.total),
        'status': i.status, 'date': i.invoice_date.strftime('%d %b')
    } for i in rows]})
