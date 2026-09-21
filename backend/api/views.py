import json
import re
from decimal import Decimal
from django.contrib.auth import authenticate
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from .auth import api_auth_required, create_token, roles_allowed
from .models import Customer, Invoice, Order, Product, Supplier, PurchaseOrder, PurchaseItem, GoodsReceipt, LedgerEntry, Warehouse, StockBalance, StockTransfer, BarcodeScanLog, WhatsAppMessage, WhatsAppOrderDraft

PERMISSIONS = {
    'OWNER': ['dashboard','products','inventory','customers','orders','invoices','purchases','ledger','warehouses','barcode','whatsapp','quotations','payments','reports','team','settings'],
    'MANAGER': ['dashboard','products','inventory','customers','orders','invoices','purchases','ledger','warehouses','barcode','whatsapp','quotations','payments','reports'],
    'SALES': ['dashboard','customers','orders','invoices','ledger','whatsapp','quotations','payments'],
    'WAREHOUSE': ['dashboard','products','inventory','orders','purchases','warehouses','barcode'],
    'ACCOUNTANT': ['dashboard','customers','orders','invoices','purchases','ledger','payments','reports'],
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


@require_GET
@roles_allowed('OWNER', 'MANAGER', 'WAREHOUSE', 'ACCOUNTANT')
def purchases(request):
    rows = PurchaseOrder.objects.select_related('supplier').prefetch_related('items').order_by('-order_date', '-id')
    return JsonResponse({'purchases': [{
        'id': po.po_no, 'supplier': po.supplier.name, 'status': po.status,
        'total': float(po.total), 'date': po.order_date.strftime('%d %b'),
        'expected': po.expected_date.strftime('%d %b') if po.expected_date else '—',
        'items': po.items.count(),
    } for po in rows]})

@require_GET
@roles_allowed('OWNER', 'MANAGER', 'WAREHOUSE', 'ACCOUNTANT')
def suppliers(request):
    rows = Supplier.objects.order_by('name')
    return JsonResponse({'suppliers': [{
        'id': s.code, 'name': s.name, 'city': s.city, 'phone': s.phone, 'gstin': s.gstin,
        'outstanding': float(s.outstanding),
    } for s in rows]})


@require_GET
@roles_allowed('OWNER', 'MANAGER', 'SALES', 'ACCOUNTANT')
def ledger(request):
    today = timezone.localdate()
    rows = LedgerEntry, Warehouse, StockBalance, StockTransfer, BarcodeScanLog, WhatsAppMessage, WhatsAppOrderDraft.objects.select_related('customer').order_by('-entry_date', '-id')
    payload = []
    for row in rows:
        age = (today - row.due_date).days if row.due_date and today > row.due_date else 0
        bucket = 'Current' if age <= 0 else ('1-30 days' if age <= 30 else ('31-60 days' if age <= 60 else ('61-90 days' if age <= 90 else '90+ days')))
        payload.append({'customer': row.customer.name, 'customerId': row.customer.code, 'type': row.entry_type, 'reference': row.reference, 'amount': float(row.amount), 'date': row.entry_date.strftime('%d %b'), 'due': row.due_date.strftime('%d %b') if row.due_date else '—', 'bucket': bucket})
    return JsonResponse({'ledger': payload})


@require_GET
@roles_allowed('OWNER', 'MANAGER', 'WAREHOUSE')
def warehouses(request):
    locations = Warehouse.objects.filter(is_active=True).order_by('name')
    transfers = StockTransfer, BarcodeScanLog, WhatsAppMessage, WhatsAppOrderDraft.objects.select_related('from_warehouse', 'to_warehouse').prefetch_related('items').order_by('-transfer_date')[:10]
    return JsonResponse({
        'warehouses': [{'id': w.code, 'name': w.name, 'city': w.city, 'stock': float(sum((b.quantity for b in w.stock_balances.all()), Decimal('0'))), 'reserved': float(sum((b.reserved for b in w.stock_balances.all()), Decimal('0')))} for w in locations.prefetch_related('stock_balances')],
        'transfers': [{'id': t.transfer_no, 'from': t.from_warehouse.name, 'to': t.to_warehouse.name, 'status': t.status, 'date': t.transfer_date.strftime('%d %b'), 'units': float(sum((i.quantity for i in t.items.all()), Decimal('0')))} for t in transfers],
    })


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@roles_allowed('OWNER', 'MANAGER', 'WAREHOUSE')
def barcode(request):
    if request.method == 'POST':
        try: body = json.loads(request.body or '{}')
        except json.JSONDecodeError: return JsonResponse({'detail': 'Invalid JSON.'}, status=400)
        code = str(body.get('code', '')).strip()
        product = Product.objects.filter(barcode=code).first() or Product.objects.filter(sku__iexact=code).first()
        if not product: return JsonResponse({'detail': 'Product not found.'}, status=404)
        warehouse = Warehouse.objects.filter(code=body.get('warehouse')).first() if body.get('warehouse') else None
        log = BarcodeScanLog, WhatsAppMessage, WhatsAppOrderDraft.objects.create(product=product, warehouse=warehouse, action=body.get('action', 'Lookup'), quantity=body.get('quantity', 1), scanned_by=request.api_user)
        return JsonResponse({'scan': {'id': log.id, 'sku': product.sku, 'name': product.name, 'barcode': product.barcode, 'action': log.action, 'quantity': float(log.quantity)}})
    rows = Product.objects.filter(is_active=True).order_by('name')
    return JsonResponse({'barcodes': [{'sku': p.sku, 'name': p.name, 'barcode': p.barcode or p.sku, 'stock': float(p.stock), 'unit': p.unit, 'location': p.location} for p in rows]})


def _parse_whatsapp_items(raw_message):
    items = []
    lowered = raw_message.lower()
    products = Product.objects.filter(is_active=True)
    for product in products:
        tokens = [token for token in re.split(r'[^a-z0-9]+', product.name.lower()) if len(token) > 2]
        sku_match = product.sku.lower() in lowered
        name_match = sum(1 for token in tokens[:4] if token in lowered) >= min(2, len(tokens[:4])) if tokens else False
        if not (sku_match or name_match):
            continue
        quantity = 1
        lines = [line for line in raw_message.splitlines() if product.sku.lower() in line.lower() or any(t in line.lower() for t in tokens[:2])]
        if lines:
            match = re.search(r'\b(\d+(?:\.\d+)?)\b', lines[0])
            if match: quantity = float(match.group(1))
        items.append({'sku': product.sku, 'name': product.name, 'quantity': quantity, 'unit': product.unit, 'price': float(product.sell_price), 'available': float(product.stock)})
    return items

@csrf_exempt
@require_http_methods(['GET', 'POST'])
@roles_allowed('OWNER', 'MANAGER', 'SALES')
def whatsapp(request):
    if request.method == 'POST':
        try: body = json.loads(request.body or '{}')
        except json.JSONDecodeError: return JsonResponse({'detail': 'Invalid JSON.'}, status=400)
        customer = Customer.objects.filter(code=body.get('customer')).first()
        raw = str(body.get('message', '')).strip()
        if not customer or not raw: return JsonResponse({'detail': 'customer and message are required.'}, status=400)
        items = _parse_whatsapp_items(raw)
        total = sum(Decimal(str(item['quantity'])) * Decimal(str(item['price'])) for item in items)
        draft_no = f'WA-{timezone.now().strftime("%y%m%d%H%M%S")}'
        draft = WhatsAppOrderDraft.objects.create(draft_no=draft_no, customer=customer, raw_message=raw, parsed_items=items, estimated_total=total)
        WhatsAppMessage.objects.create(customer=customer, direction='Inbound', message=raw, status='Received')
        return JsonResponse({'draft': {'id': draft.draft_no, 'customer': customer.name, 'items': items, 'total': float(total), 'status': draft.status}}, status=201)
    drafts = WhatsAppOrderDraft.objects.select_related('customer').order_by('-created_at')[:12]
    return JsonResponse({'whatsapp': [{'id': d.draft_no, 'customer': d.customer.name, 'message': d.raw_message, 'items': d.parsed_items, 'total': float(d.estimated_total), 'status': d.status} for d in drafts]})
