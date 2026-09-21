import csv
import io
import json
import os
import re
import urllib.error
import urllib.request
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import F, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from .auth import (
    api_auth_required, create_session_tokens, refresh_access_token, create_portal_token, portal_auth_required,
    revoke_request_session, roles_allowed,
)
from .models import (
    AccountingConnection, AccountingExportJob, ApprovalPolicy, AssistantMessage, AssistantThread, CompanySubscription, OfflineSyncReceipt, SubscriptionInvoice, SubscriptionPlan, ApprovalRequest, Attachment, AuditLog, PurchaseInvoiceCapture, BarcodeScanLog, Branch, Company, Customer, CustomerPortalAccess, CustomerPortalOrder, DeliveryProof, DeliveryRun, DeliveryStop, GoodsReceipt,
    GoodsReceiptItem, InventoryMovement, Invoice, LedgerEntry, Notification, Order,
    OrderItem, Payment, PriceList, PriceRule, Product, PurchaseItem, PurchaseOrder,
    Quotation, QuotationItem, ReorderSuggestion, ReturnItem, ReturnOrder, SalesTarget,
    SalesVisit, StockAdjustment, StockBalance, StockTransfer, StockTransferItem,
    Supplier, SupplierLedgerEntry, SupplierPayment, TaxNote, Warehouse, WhatsAppMessage,
    WhatsAppOrderDraft,
)
from .services import (
    apply_stock, audit, calculate_line, create_order_items, decimal, dispatch_order,
    notify, release_order_stock, reserve_order_stock,
)

PERMISSIONS = {
    'OWNER': ['dashboard','products','inventory','customers','orders','invoices','purchases','ledger','warehouses','barcode','whatsapp','tax','pricing','returns','field-sales','insights','quotations','payments','reports','team','settings','audit','delivery','approvals','invoice-ocr','accounting','offline','subscription','forecasting','assistant','collections'],
    'MANAGER': ['dashboard','products','inventory','customers','orders','invoices','purchases','ledger','warehouses','barcode','whatsapp','tax','pricing','returns','field-sales','insights','quotations','payments','reports','audit','delivery','approvals','invoice-ocr','accounting','offline','forecasting','assistant','collections'],
    'SALES': ['dashboard','customers','orders','invoices','ledger','whatsapp','tax','pricing','field-sales','quotations','payments','delivery','approvals','offline','assistant','collections'],
    'WAREHOUSE': ['dashboard','products','inventory','orders','purchases','warehouses','barcode','returns','insights','delivery','approvals','invoice-ocr','offline','forecasting'],
    'ACCOUNTANT': ['dashboard','customers','orders','invoices','purchases','ledger','tax','returns','insights','payments','reports','audit','approvals','invoice-ocr','accounting','assistant','collections'],
}


def _json_body(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return None


def _date(value, default=None):
    if not value:
        return default or timezone.localdate()
    try:
        return timezone.datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except ValueError:
        return default or timezone.localdate()


def _next_no(prefix):
    return f'{prefix}-{timezone.now().strftime("%y%m%d%H%M%S%f")[-14:]}'


def _page(request, qs, serializer, default_size=50):
    try:
        page = max(1, int(request.GET.get('page', 1)))
        size = min(100, max(1, int(request.GET.get('page_size', default_size))))
    except ValueError:
        page, size = 1, default_size
    total = qs.count()
    start = (page - 1) * size
    rows = [serializer(x) for x in qs[start:start + size]]
    return {'results': rows, 'page': page, 'pageSize': size, 'total': total, 'pages': max(1, (total + size - 1) // size)}


def _company_qs(model, request):
    return model.objects.filter(company=request.company)


def user_payload(user):
    profile = user.profile
    company = profile.company
    permissions = list(dict.fromkeys(PERMISSIONS.get(profile.role, []) + (profile.extra_permissions or [])))
    return {
        'id': user.id,
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'role': profile.role,
        'business': company.name if company else profile.business_name,
        'companyId': company.id if company else None,
        'branch': {'id': profile.branch_id, 'name': profile.branch.name} if profile.branch else None,
        'permissions': permissions,
        'branding': {'logo': company.logo_url, 'state': company.state, 'invoicePrefix': company.invoice_prefix} if company else {},
    }


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        database = 'ok'
    except Exception:
        database = 'error'
    status = 200 if database == 'ok' else 503
    return JsonResponse({'ok': database == 'ok', 'service': 'setustock-api', 'database': database, 'time': timezone.now().isoformat()}, status=status)


@csrf_exempt
@require_POST
def login_view(request):
    body = _json_body(request)
    if body is None:
        return JsonResponse({'detail': 'Invalid JSON.'}, status=400)
    email = str(body.get('email', '')).strip().lower()
    password = str(body.get('password', ''))
    if not email or not password:
        return JsonResponse({'detail': 'Email and password are required.'}, status=400)
    guard_key = f"login-guard:{email}:{request.META.get('REMOTE_ADDR', 'unknown')}"
    attempts = cache.get(guard_key, 0)
    max_attempts = int(os.getenv('LOGIN_MAX_ATTEMPTS', '5'))
    if attempts >= max_attempts:
        return JsonResponse({'detail': 'Too many failed login attempts. Try again later.'}, status=429)
    account = User.objects.filter(email__iexact=email, is_active=True).select_related('profile__company', 'profile__branch').first()
    if not account:
        cache.set(guard_key, attempts + 1, int(os.getenv('LOGIN_LOCK_SECONDS', '900')))
        return JsonResponse({'detail': 'Invalid email or password.'}, status=401)
    user = authenticate(request, username=account.username, password=password)
    if not user:
        cache.set(guard_key, attempts + 1, int(os.getenv('LOGIN_LOCK_SECONDS', '900')))
        return JsonResponse({'detail': 'Invalid email or password.'}, status=401)
    cache.delete(guard_key)
    if not hasattr(user, 'profile') or not user.profile.company:
        return JsonResponse({'detail': 'Account setup is incomplete. Contact your administrator.'}, status=403)
    access, refresh = create_session_tokens(user, request)
    return JsonResponse({'token': access, 'refreshToken': refresh, 'user': user_payload(user)})


@csrf_exempt
@require_POST
def password_reset_request(request):
    body = _json_body(request) or {}
    email = str(body.get('email', '')).strip().lower()
    user = User.objects.filter(email__iexact=email, is_active=True).first() if email else None
    # Always return the same response so account existence is not disclosed.
    response = {'ok': True, 'detail': 'If that account exists, password reset instructions have been sent.'}
    if not user:
        return JsonResponse(response)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    frontend = os.getenv('FRONTEND_URL', 'http://localhost:5173').rstrip('/')
    reset_url = f'{frontend}/login?reset_uid={uid}&reset_token={token}'
    try:
        send_mail(
            'SetuStock password reset',
            f'Use this link to reset your SetuStock password: {reset_url}',
            os.getenv('DEFAULT_FROM_EMAIL', 'noreply@setustock.local'),
            [user.email],
            fail_silently=True,
        )
    except Exception:
        pass
    if settings.DEBUG or os.getenv('SETUSTOCK_DEMO_MODE', 'false').lower() == 'true':
        response['demoReset'] = {'uid': uid, 'token': token, 'url': reset_url}
    return JsonResponse(response)


@csrf_exempt
@require_POST
def password_reset_confirm(request):
    body = _json_body(request) or {}
    uid = str(body.get('uid', ''))
    token = str(body.get('token', ''))
    new_password = str(body.get('newPassword', ''))
    if len(new_password) < 8:
        return JsonResponse({'detail': 'New password must be at least 8 characters.'}, status=400)
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id, is_active=True)
    except (ValueError, TypeError, User.DoesNotExist):
        return JsonResponse({'detail': 'Reset link is invalid or expired.'}, status=400)
    if not default_token_generator.check_token(user, token):
        return JsonResponse({'detail': 'Reset link is invalid or expired.'}, status=400)
    user.set_password(new_password)
    user.save(update_fields=['password'])
    from .models import AuthSession
    AuthSession.objects.filter(user=user, revoked_at__isnull=True).update(revoked_at=timezone.now())
    return JsonResponse({'ok': True})


@csrf_exempt
@require_POST
def refresh_token(request):
    body = _json_body(request) or {}
    access, user = refresh_access_token(str(body.get('refreshToken', '')))
    if not access or not user:
        return JsonResponse({'detail': 'Refresh token is invalid or expired.'}, status=401)
    return JsonResponse({'token': access, 'user': user_payload(user)})


@csrf_exempt
@require_POST
@api_auth_required
def logout_view(request):
    revoke_request_session(request)
    return JsonResponse({'ok': True})


@csrf_exempt
@require_POST
@api_auth_required
def change_password(request):
    body = _json_body(request) or {}
    current = str(body.get('currentPassword', ''))
    new_password = str(body.get('newPassword', ''))
    if not request.api_user.check_password(current):
        return JsonResponse({'detail': 'Current password is incorrect.'}, status=400)
    if len(new_password) < 8:
        return JsonResponse({'detail': 'New password must be at least 8 characters.'}, status=400)
    request.api_user.set_password(new_password)
    request.api_user.save(update_fields=['password'])
    audit(request, 'password_change', 'User', request.api_user.id, 'Password changed')
    return JsonResponse({'ok': True})


@require_GET
@api_auth_required
def me(request):
    return JsonResponse({'user': user_payload(request.api_user)})


@require_GET
@api_auth_required
def dashboard(request):
    today = timezone.localdate()
    orders_qs = _company_qs(Order, request)
    customers_qs = _company_qs(Customer, request)
    products_qs = _company_qs(Product, request).filter(is_active=True)
    sales_today = orders_qs.filter(order_date=today).aggregate(total=Sum('total'))['total'] or Decimal('0')
    sales_month = orders_qs.filter(order_date__year=today.year, order_date__month=today.month).aggregate(total=Sum('total'))['total'] or Decimal('0')
    receivable = customers_qs.aggregate(total=Sum('outstanding'))['total'] or Decimal('0')
    stock_value = sum((p.stock * p.purchase_price for p in products_qs), Decimal('0'))
    low_stock = sum(1 for p in products_qs if p.stock <= p.reorder_level)
    recent = orders_qs.select_related('customer').order_by('-order_date', '-id')[:8]
    unread = Notification.objects.filter(company=request.company, is_read=False).filter(Q(user=request.api_user) | Q(user__isnull=True)).count()
    return JsonResponse({
        'metrics': {'salesToday': float(sales_today), 'salesMonth': float(sales_month), 'receivable': float(receivable), 'stockValue': float(stock_value), 'openOrders': orders_qs.exclude(status__in=[Order.Status.DISPATCHED, Order.Status.CANCELLED]).count(), 'lowStock': low_stock, 'unreadNotifications': unread},
        'recentOrders': [_serialize_order(o) for o in recent],
    })


def _serialize_product(p):
    return {'id': p.id, 'sku': p.sku, 'name': p.name, 'category': p.category, 'stock': float(p.stock), 'unit': p.unit, 'buy': float(p.purchase_price), 'sell': float(p.sell_price), 'reorder': float(p.reorder_level), 'location': p.location, 'barcode': p.barcode or '', 'hsn': p.hsn_code, 'gstRate': float(p.gst_rate), 'image': p.image_url}


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@roles_allowed('OWNER', 'MANAGER', 'WAREHOUSE', 'SALES', 'ACCOUNTANT')
def products(request):
    if request.method == 'POST':
        if request.api_user.profile.role not in ['OWNER', 'MANAGER', 'WAREHOUSE']:
            return JsonResponse({'detail': 'You have read-only access to the product catalogue.'}, status=403)
        body = _json_body(request)
        if body is None or not body.get('sku') or not body.get('name'):
            return JsonResponse({'detail': 'sku and name are required.'}, status=400)
        try:
            product = Product.objects.create(
                company=request.company, sku=str(body['sku']).strip(), name=str(body['name']).strip(),
                category=body.get('category', ''), unit=body.get('unit', 'pcs'), purchase_price=decimal(body.get('buy')),
                sell_price=decimal(body.get('sell')), reorder_level=decimal(body.get('reorder')), location=body.get('location', ''),
                barcode=(str(body.get('barcode')).strip() or None) if body.get('barcode') is not None else None,
                hsn_code=body.get('hsn', ''), gst_rate=decimal(body.get('gstRate', 18)), image_url=body.get('image', ''),
            )
        except Exception as exc:
            return JsonResponse({'detail': f'Could not create product: {exc}'}, status=400)
        audit(request, 'create', 'Product', product.id, f'Created product {product.sku}', {'sku': product.sku})
        return JsonResponse({'product': _serialize_product(product)}, status=201)
    q = request.GET.get('q', '').strip()
    rows = _company_qs(Product, request).filter(is_active=True)
    if q:
        rows = rows.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(category__icontains=q) | Q(barcode__icontains=q))
    rows = rows.order_by('name')
    return JsonResponse({'products': [_serialize_product(p) for p in rows]})


@csrf_exempt
@require_http_methods(['PATCH', 'DELETE'])
@roles_allowed('OWNER', 'MANAGER')
def product_detail(request, pk):
    product = _company_qs(Product, request).filter(pk=pk).first()
    if not product:
        return JsonResponse({'detail': 'Product not found.'}, status=404)
    if request.method == 'DELETE':
        product.is_active = False
        product.save(update_fields=['is_active'])
        audit(request, 'archive', 'Product', product.id, f'Archived {product.sku}')
        return JsonResponse({'ok': True})
    body = _json_body(request) or {}
    mapping = {'name':'name','category':'category','unit':'unit','location':'location','hsn':'hsn_code','image':'image_url'}
    for src, dest in mapping.items():
        if src in body:
            setattr(product, dest, body[src])
    if 'buy' in body: product.purchase_price = decimal(body['buy'])
    if 'sell' in body: product.sell_price = decimal(body['sell'])
    if 'reorder' in body: product.reorder_level = decimal(body['reorder'])
    if 'gstRate' in body: product.gst_rate = decimal(body['gstRate'])
    if 'barcode' in body: product.barcode = body['barcode'] or None
    product.save()
    audit(request, 'update', 'Product', product.id, f'Updated {product.sku}', body)
    return JsonResponse({'product': _serialize_product(product)})


def _serialize_customer(c):
    status = 'Overdue' if c.outstanding and c.due_date and c.due_date < timezone.localdate() else ('Current' if c.outstanding else 'Clear')
    return {'pk': c.id, 'id': c.code, 'name': c.name, 'city': c.city, 'state': c.state, 'address': c.address, 'phone': c.phone, 'email': c.email, 'gstin': c.gstin, 'outstanding': float(c.outstanding), 'limit': float(c.credit_limit), 'due': c.due_date.strftime('%d %b') if c.due_date else '—', 'status': status}


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@roles_allowed('OWNER', 'MANAGER', 'SALES', 'ACCOUNTANT')
def customers(request):
    if request.method == 'POST':
        body = _json_body(request) or {}
        if not body.get('code') or not body.get('name'):
            return JsonResponse({'detail': 'code and name are required.'}, status=400)
        try:
            customer = Customer.objects.create(company=request.company, code=body['code'], name=body['name'], city=body.get('city',''), state=body.get('state', request.company.state), address=body.get('address',''), phone=body.get('phone',''), email=body.get('email',''), gstin=body.get('gstin',''), credit_limit=decimal(body.get('credit_limit', body.get('limit', 0))))
        except Exception as exc:
            return JsonResponse({'detail': f'Could not create customer: {exc}'}, status=400)
        audit(request, 'create', 'Customer', customer.id, f'Created customer {customer.code}')
        return JsonResponse({'customer': _serialize_customer(customer)}, status=201)
    q = request.GET.get('q', '').strip()
    rows = _company_qs(Customer, request).filter(is_active=True)
    if q:
        rows = rows.filter(Q(name__icontains=q)|Q(code__icontains=q)|Q(phone__icontains=q)|Q(city__icontains=q)|Q(gstin__icontains=q))
    return JsonResponse({'customers': [_serialize_customer(c) for c in rows.order_by('name')]})


@csrf_exempt
@require_http_methods(['PATCH', 'DELETE'])
@roles_allowed('OWNER', 'MANAGER', 'ACCOUNTANT')
def customer_detail(request, pk):
    customer = _company_qs(Customer, request).filter(pk=pk).first()
    if not customer:
        return JsonResponse({'detail': 'Customer not found.'}, status=404)
    if request.method == 'DELETE':
        customer.is_active = False; customer.save(update_fields=['is_active'])
        audit(request, 'archive', 'Customer', customer.id, f'Archived {customer.code}')
        return JsonResponse({'ok': True})
    body = _json_body(request) or {}
    for key in ['name','city','state','address','phone','email','gstin']:
        if key in body: setattr(customer, key, body[key])
    if 'credit_limit' in body: customer.credit_limit = decimal(body['credit_limit'])
    customer.save()
    audit(request, 'update', 'Customer', customer.id, f'Updated {customer.code}', body)
    return JsonResponse({'customer': _serialize_customer(customer)})


def _serialize_order(o, include_items=False):
    data = {'pk': o.id, 'id': o.order_no, 'customer': o.customer.name, 'customerId': o.customer.code, 'total': float(o.total), 'subtotal': float(o.subtotal), 'tax': float(o.tax), 'status': o.status, 'payment': o.payment_status, 'date': o.order_date.strftime('%d %b'), 'warehouse': o.warehouse.name if o.warehouse else '—', 'reserved': o.stock_reserved}
    if include_items:
        data['items'] = [{'id': i.id, 'productId': i.product_id, 'sku': i.product.sku, 'product': i.product.name, 'quantity': float(i.quantity), 'unitPrice': float(i.unit_price), 'taxable': float(i.taxable_amount), 'tax': float(i.tax_amount), 'total': float(i.line_total)} for i in o.items.select_related('product')]
    return data


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@roles_allowed('OWNER', 'MANAGER', 'SALES', 'WAREHOUSE', 'ACCOUNTANT')
def orders(request):
    if request.method == 'POST':
        if request.api_user.profile.role == 'ACCOUNTANT':
            return JsonResponse({'detail': 'Accountant role cannot create sales orders.'}, status=403)
        body = _json_body(request) or {}
        customer = _company_qs(Customer, request).filter(pk=body.get('customerId')).first() or _company_qs(Customer, request).filter(code=body.get('customer')).first()
        warehouse = _company_qs(Warehouse, request).filter(pk=body.get('warehouseId')).first() or _company_qs(Warehouse, request).filter(code=body.get('warehouse')).first()
        items = body.get('items') or []
        if not customer or not warehouse or not items:
            return JsonResponse({'detail': 'customer, warehouse and at least one item are required.'}, status=400)
        with transaction.atomic():
            order = Order.objects.create(company=request.company, branch=request.branch, warehouse=warehouse, order_no=body.get('orderNo') or _next_no('SO'), customer=customer, order_date=_date(body.get('orderDate')), notes=body.get('notes',''), discount=decimal(body.get('discount')), created_by=request.api_user)
            try:
                create_order_items(order, items)
                if body.get('confirm'):
                    reserve_order_stock(order, request.api_user)
                    order.status = Order.Status.CONFIRMED; order.save(update_fields=['status','updated_at'])
            except (Product.DoesNotExist, ValueError) as exc:
                transaction.set_rollback(True)
                return JsonResponse({'detail': str(exc)}, status=400)
        audit(request, 'create', 'Order', order.id, f'Created order {order.order_no}', {'total': float(order.total)})
        return JsonResponse({'order': _serialize_order(order, True)}, status=201)
    rows = _company_qs(Order, request).select_related('customer','warehouse').prefetch_related('items__product').order_by('-order_date','-id')
    q = request.GET.get('q','').strip()
    if q: rows = rows.filter(Q(order_no__icontains=q)|Q(customer__name__icontains=q)|Q(customer__code__icontains=q))
    return JsonResponse({'orders': [_serialize_order(o, request.GET.get('detail') == '1') for o in rows]})


@csrf_exempt
@require_POST
@roles_allowed('OWNER', 'MANAGER', 'SALES', 'WAREHOUSE')
def order_action(request, pk):
    order = _company_qs(Order, request).select_related('warehouse').prefetch_related('items__product').filter(pk=pk).first()
    if not order:
        return JsonResponse({'detail': 'Order not found.'}, status=404)
    body = _json_body(request) or {}
    action = body.get('action')
    try:
        if action == 'confirm':
            reserve_order_stock(order, request.api_user); order.status = Order.Status.CONFIRMED; order.save(update_fields=['status','updated_at'])
        elif action in ['processing','packed','ready']:
            status_map = {'processing':Order.Status.PROCESSING,'packed':Order.Status.PACKED,'ready':Order.Status.READY}
            if not order.stock_reserved: reserve_order_stock(order, request.api_user)
            order.status = status_map[action]; order.save(update_fields=['status','updated_at'])
        elif action == 'dispatch':
            dispatch_order(order, request.api_user)
        elif action == 'cancel':
            if order.status == Order.Status.DISPATCHED: return JsonResponse({'detail':'Dispatched orders cannot be cancelled.'}, status=400)
            release_order_stock(order, request.api_user); order.status = Order.Status.CANCELLED; order.save(update_fields=['status','updated_at'])
        else:
            return JsonResponse({'detail':'Unknown order action.'}, status=400)
    except ValueError as exc:
        return JsonResponse({'detail': str(exc)}, status=400)
    audit(request, action, 'Order', order.id, f'{action.title()} order {order.order_no}')
    return JsonResponse({'order': _serialize_order(order, True)})


def _serialize_invoice(i):
    return {'pk': i.id, 'id': i.invoice_no, 'order': i.order.order_no, 'orderPk': i.order_id, 'customer': i.order.customer.name, 'gstin': i.gstin, 'taxable': float(i.taxable_amount), 'cgst': float(i.cgst), 'sgst': float(i.sgst), 'igst': float(i.igst), 'tax': float(i.cgst+i.sgst+i.igst), 'total': float(i.total), 'status': i.status, 'date': i.invoice_date.strftime('%d %b'), 'dueDate': i.due_date.isoformat() if i.due_date else None, 'supplyType': i.supply_type, 'placeOfSupply': i.place_of_supply}


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','SALES','ACCOUNTANT')
def invoices(request):
    if request.method == 'POST':
        body = _json_body(request) or {}
        order = _company_qs(Order, request).select_related('customer').filter(pk=body.get('orderId')).first() or _company_qs(Order, request).select_related('customer').filter(order_no=body.get('order')).first()
        if not order:
            return JsonResponse({'detail':'Order is required.'}, status=400)
        if hasattr(order, 'invoice'):
            return JsonResponse({'detail':'This order already has an invoice.'}, status=400)
        taxable = order.subtotal
        total_tax = order.tax
        supply_type = body.get('supplyType','Intra-state')
        if supply_type == 'Inter-state': cgst=sgst=Decimal('0'); igst=total_tax
        else: cgst=(total_tax/2).quantize(Decimal('0.01')); sgst=total_tax-cgst; igst=Decimal('0')
        due_date = _date(body.get('dueDate'), order.order_date + timedelta(days=30))
        invoice = Invoice.objects.create(company=request.company, invoice_no=body.get('invoiceNo') or _next_no(request.company.invoice_prefix or 'INV'), order=order, gstin=order.customer.gstin, taxable_amount=taxable, cgst=cgst, sgst=sgst, igst=igst, total=order.total, status=Invoice.Status.UNPAID, invoice_date=_date(body.get('invoiceDate')), due_date=due_date, place_of_supply=body.get('placeOfSupply', order.customer.state), supply_type=supply_type, terms=body.get('terms','Payment due within 30 days.'), notes=body.get('notes',''), qr_payload=f'upi://pay?pa={request.company.upi_id}&am={order.total}&tn={order.order_no}' if request.company.upi_id else '')
        LedgerEntry.objects.create(company=request.company, customer=order.customer, entry_type=LedgerEntry.EntryType.INVOICE, reference=invoice.invoice_no, amount=invoice.total, entry_date=invoice.invoice_date, due_date=due_date, note=f'Invoice for {order.order_no}')
        Customer.objects.filter(pk=order.customer_id).update(outstanding=F('outstanding') + invoice.total, due_date=due_date)
        audit(request,'create','Invoice',invoice.id,f'Created invoice {invoice.invoice_no}')
        return JsonResponse({'invoice':_serialize_invoice(invoice)},status=201)
    rows = _company_qs(Invoice, request).select_related('order__customer').order_by('-invoice_date','-id')
    return JsonResponse({'invoices': [_serialize_invoice(i) for i in rows]})


@require_GET
@roles_allowed('OWNER','MANAGER','SALES','ACCOUNTANT')
def invoice_print(request, pk):
    invoice = _company_qs(Invoice, request).select_related('order__customer').prefetch_related('order__items__product').filter(pk=pk).first()
    if not invoice:
        return HttpResponse('Invoice not found', status=404)
    c, customer = request.company, invoice.order.customer
    item_rows = ''.join(f"<tr><td>{escape(x.product.name)}<br><small>{escape(x.product.sku)} · HSN {escape(x.product.hsn_code or '—')}</small></td><td>{x.quantity}</td><td>₹{x.unit_price}</td><td>{x.gst_rate}%</td><td>₹{x.line_total}</td></tr>" for x in invoice.order.items.all())
    html = f'''<!doctype html><html><head><meta charset="utf-8"><title>{escape(invoice.invoice_no)}</title><style>body{{font-family:Arial,sans-serif;color:#173a3a;margin:36px}}.head{{display:flex;justify-content:space-between;border-bottom:3px solid #0f615c;padding-bottom:18px}}h1{{margin:0;color:#0f615c}}table{{width:100%;border-collapse:collapse;margin-top:24px}}th,td{{padding:10px;border-bottom:1px solid #d9e3de;text-align:left}}.totals{{margin-left:auto;width:340px;margin-top:20px}}.totals div{{display:flex;justify-content:space-between;padding:6px}}.grand{{font-size:20px;font-weight:700;border-top:2px solid #173a3a}}.print{{position:fixed;right:28px;top:20px}}@media print{{.print{{display:none}}body{{margin:0}}}}</style></head><body><button class="print" onclick="print()">Print / Save PDF</button><div class="head"><div><h1>{escape(c.name)}</h1><p>{escape(c.address)}<br>GSTIN: {escape(c.gstin or '—')} · {escape(c.phone)}</p></div><div><h2>Tax Invoice</h2><b>{escape(invoice.invoice_no)}</b><p>{invoice.invoice_date}<br>Due: {invoice.due_date or '—'}</p></div></div><p><b>Bill to:</b><br>{escape(customer.name)}<br>{escape(customer.address or customer.city)}<br>GSTIN: {escape(customer.gstin or '—')}</p><table><thead><tr><th>Item</th><th>Qty</th><th>Rate</th><th>GST</th><th>Total</th></tr></thead><tbody>{item_rows}</tbody></table><div class="totals"><div><span>Taxable</span><b>₹{invoice.taxable_amount}</b></div><div><span>CGST</span><b>₹{invoice.cgst}</b></div><div><span>SGST</span><b>₹{invoice.sgst}</b></div><div><span>IGST</span><b>₹{invoice.igst}</b></div><div class="grand"><span>Total</span><b>₹{invoice.total}</b></div></div><p><b>Bank / UPI:</b> {escape(c.bank_name)} {escape(c.upi_id)}</p><p><b>Terms:</b> {escape(invoice.terms)}</p></body></html>'''
    return HttpResponse(html, content_type='text/html')


def _serialize_supplier(s):
    return {'pk':s.id,'id':s.code,'name':s.name,'city':s.city,'state':s.state,'phone':s.phone,'email':s.email,'gstin':s.gstin,'outstanding':float(s.outstanding)}


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','WAREHOUSE','ACCOUNTANT')
def suppliers(request):
    if request.method == 'POST':
        body=_json_body(request) or {}
        if not body.get('code') or not body.get('name'): return JsonResponse({'detail':'code and name are required.'},status=400)
        try: supplier=Supplier.objects.create(company=request.company,code=body['code'],name=body['name'],city=body.get('city',''),state=body.get('state',request.company.state),address=body.get('address',''),phone=body.get('phone',''),email=body.get('email',''),gstin=body.get('gstin',''))
        except Exception as exc: return JsonResponse({'detail':str(exc)},status=400)
        audit(request,'create','Supplier',supplier.id,f'Created supplier {supplier.code}')
        return JsonResponse({'supplier':_serialize_supplier(supplier)},status=201)
    return JsonResponse({'suppliers':[_serialize_supplier(s) for s in _company_qs(Supplier,request).order_by('name')]})


def _serialize_purchase(po):
    return {'pk':po.id,'id':po.po_no,'supplier':po.supplier.name,'supplierId':po.supplier_id,'status':po.status,'total':float(po.total),'date':po.order_date.strftime('%d %b'),'expected':po.expected_date.strftime('%d %b') if po.expected_date else '—','items':po.items.count(),'warehouse':po.warehouse.name if po.warehouse else '—','lines':[{'id':i.id,'productId':i.product_id,'sku':i.product.sku,'product':i.product.name,'quantity':float(i.quantity),'received':float(i.received_quantity),'unitPrice':float(i.unit_price)} for i in po.items.select_related('product').all()]}


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','WAREHOUSE','ACCOUNTANT')
def purchases(request):
    if request.method == 'POST':
        if request.api_user.profile.role == 'ACCOUNTANT': return JsonResponse({'detail':'Accountant role cannot create purchase orders.'},status=403)
        body=_json_body(request) or {}
        supplier=_company_qs(Supplier,request).filter(pk=body.get('supplierId')).first() or _company_qs(Supplier,request).filter(code=body.get('supplier')).first()
        warehouse=_company_qs(Warehouse,request).filter(pk=body.get('warehouseId')).first() or _company_qs(Warehouse,request).filter(code=body.get('warehouse')).first()
        items=body.get('items') or []
        if not supplier or not warehouse or not items: return JsonResponse({'detail':'supplier, warehouse and items are required.'},status=400)
        with transaction.atomic():
            po=PurchaseOrder.objects.create(company=request.company,branch=request.branch,warehouse=warehouse,po_no=body.get('poNo') or _next_no('PO'),supplier=supplier,order_date=_date(body.get('orderDate')),expected_date=_date(body.get('expectedDate')) if body.get('expectedDate') else None,notes=body.get('notes',''),created_by=request.api_user)
            total=Decimal('0')
            for row in items:
                product=_company_qs(Product,request).filter(pk=row.get('product_id') or row.get('productId'),is_active=True).first()
                if not product: transaction.set_rollback(True); return JsonResponse({'detail':'Invalid product in purchase order.'},status=400)
                qty=decimal(row.get('quantity')); price=decimal(row.get('unit_price',row.get('unitPrice',product.purchase_price)))
                PurchaseItem.objects.create(purchase=po,product=product,quantity=qty,unit_price=price)
                total += qty*price
            po.total=total; po.save(update_fields=['total'])
        audit(request,'create','PurchaseOrder',po.id,f'Created {po.po_no}')
        return JsonResponse({'purchase':_serialize_purchase(po)},status=201)
    rows=_company_qs(PurchaseOrder,request).select_related('supplier','warehouse').prefetch_related('items__product').order_by('-order_date','-id')
    return JsonResponse({'purchases':[_serialize_purchase(po) for po in rows]})


@csrf_exempt
@require_POST
@roles_allowed('OWNER','MANAGER','WAREHOUSE')
def purchase_action(request, pk):
    po=_company_qs(PurchaseOrder,request).select_related('supplier','warehouse').prefetch_related('items__product').filter(pk=pk).first()
    if not po: return JsonResponse({'detail':'Purchase order not found.'},status=404)
    body=_json_body(request) or {}; action=body.get('action')
    if action=='approve':
        po.status=PurchaseOrder.Status.APPROVED; po.approved_by=request.api_user; po.approved_at=timezone.now(); po.save(update_fields=['status','approved_by','approved_at']); audit(request,'approve','PurchaseOrder',po.id,f'Approved {po.po_no}'); return JsonResponse({'purchase':_serialize_purchase(po)})
    if action!='receive': return JsonResponse({'detail':'Unknown purchase action.'},status=400)
    if po.status not in [PurchaseOrder.Status.APPROVED, PurchaseOrder.Status.PARTIAL]:
        return JsonResponse({'detail':'Purchase order must be approved before receiving goods.'},status=400)
    if not po.warehouse: return JsonResponse({'detail':'Purchase order has no receiving warehouse.'},status=400)
    quantities=body.get('items') or []
    receipt_map={int(x.get('purchaseItemId')):decimal(x.get('quantity')) for x in quantities if x.get('purchaseItemId')}
    with transaction.atomic():
        receipt=GoodsReceipt.objects.create(grn_no=body.get('grnNo') or _next_no('GRN'),purchase=po,warehouse=po.warehouse,received_date=_date(body.get('date')),notes=body.get('notes',''),received_by=request.api_user)
        receipt_value=Decimal('0')
        for item in po.items.select_for_update().select_related('product'):
            qty=receipt_map.get(item.id, max(Decimal('0'), item.quantity-item.received_quantity))
            remaining=item.quantity-item.received_quantity
            if qty<=0: continue
            if qty>remaining: return JsonResponse({'detail':f'Receipt exceeds remaining quantity for {item.product.sku}.'},status=400)
            GoodsReceiptItem.objects.create(receipt=receipt,purchase_item=item,quantity=qty)
            item.received_quantity += qty; item.save(update_fields=['received_quantity'])
            apply_stock(request.company,po.warehouse,item.product,qty,InventoryMovement.MovementType.PURCHASE,receipt.grn_no,request.api_user,'Goods receipt')
            receipt_value += qty*item.unit_price
        complete=all(x.received_quantity>=x.quantity for x in po.items.all())
        po.status=PurchaseOrder.Status.RECEIVED if complete else PurchaseOrder.Status.PARTIAL; po.save(update_fields=['status'])
        po.supplier.outstanding += receipt_value; po.supplier.save(update_fields=['outstanding'])
        SupplierLedgerEntry.objects.create(company=request.company,supplier=po.supplier,entry_type='Purchase',reference=receipt.grn_no,amount=receipt_value,entry_date=receipt.received_date,note=f'Receipt against {po.po_no}')
    audit(request,'receive','PurchaseOrder',po.id,f'Received goods for {po.po_no}',{'grn':receipt.grn_no,'value':float(receipt_value)})
    return JsonResponse({'purchase':_serialize_purchase(po),'grn':receipt.grn_no})


@require_GET
@roles_allowed('OWNER','MANAGER','SALES','ACCOUNTANT')
def ledger(request):
    today=timezone.localdate(); rows=_company_qs(LedgerEntry,request).select_related('customer').order_by('-entry_date','-id')
    payload=[]
    for row in rows:
        age=(today-row.due_date).days if row.due_date and today>row.due_date else 0
        bucket='Current' if age<=0 else ('1-30 days' if age<=30 else ('31-60 days' if age<=60 else ('61-90 days' if age<=90 else '90+ days')))
        payload.append({'id':row.id,'customer':row.customer.name,'customerId':row.customer.code,'type':row.entry_type,'reference':row.reference,'amount':float(row.amount),'date':row.entry_date.strftime('%d %b'),'due':row.due_date.strftime('%d %b') if row.due_date else '—','bucket':bucket})
    return JsonResponse({'ledger':payload})


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','SALES','ACCOUNTANT')
def payments(request):
    if request.method=='POST':
        body=_json_body(request) or {}; party=body.get('partyType','customer')
        if party=='supplier':
            if request.api_user.profile.role=='SALES': return JsonResponse({'detail':'Sales role cannot record supplier payments.'},status=403)
            supplier=_company_qs(Supplier,request).filter(pk=body.get('supplierId')).first()
            amount=decimal(body.get('amount'))
            if not supplier or amount<=0: return JsonResponse({'detail':'supplier and positive amount are required.'},status=400)
            payment=SupplierPayment.objects.create(company=request.company,payment_no=body.get('paymentNo') or _next_no('SPAY'),supplier=supplier,amount=amount,method=body.get('method','Bank'),reference=body.get('reference',''),payment_date=_date(body.get('date')),notes=body.get('notes',''),recorded_by=request.api_user)
            supplier.outstanding=max(Decimal('0'),supplier.outstanding-amount); supplier.save(update_fields=['outstanding'])
            SupplierLedgerEntry.objects.create(company=request.company,supplier=supplier,entry_type='Payment',reference=payment.payment_no,amount=-amount,entry_date=payment.payment_date,note=payment.notes)
            audit(request,'create','SupplierPayment',payment.id,f'Recorded {payment.payment_no}')
            return JsonResponse({'payment':{'id':payment.payment_no,'party':supplier.name,'amount':float(amount),'method':payment.method,'date':payment.payment_date.isoformat(),'partyType':'supplier'}},status=201)
        customer=_company_qs(Customer,request).filter(pk=body.get('customerId')).first()
        amount=decimal(body.get('amount'))
        if not customer or amount<=0: return JsonResponse({'detail':'customer and positive amount are required.'},status=400)
        invoice=_company_qs(Invoice,request).filter(pk=body.get('invoiceId'),order__customer=customer).first() if body.get('invoiceId') else None
        payment=Payment.objects.create(company=request.company,receipt_no=body.get('receiptNo') or _next_no('RCPT'),customer=customer,invoice=invoice,amount=amount,method=body.get('method','Bank'),reference=body.get('reference',''),payment_date=_date(body.get('date')),notes=body.get('notes',''),recorded_by=request.api_user)
        customer.outstanding=max(Decimal('0'),customer.outstanding-amount); customer.save(update_fields=['outstanding'])
        LedgerEntry.objects.create(company=request.company,customer=customer,entry_type=LedgerEntry.EntryType.PAYMENT,reference=payment.receipt_no,amount=-amount,entry_date=payment.payment_date,note=payment.notes)
        if invoice:
            paid=invoice.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
            invoice.status=Invoice.Status.PAID if paid>=invoice.total else Invoice.Status.PARTIAL; invoice.save(update_fields=['status','updated_at'])
            invoice.order.payment_status=Order.PaymentStatus.PAID if paid>=invoice.total else Order.PaymentStatus.PARTIAL; invoice.order.save(update_fields=['payment_status','updated_at'])
        audit(request,'create','Payment',payment.id,f'Recorded receipt {payment.receipt_no}',{'amount':float(amount)})
        return JsonResponse({'payment':{'id':payment.receipt_no,'party':customer.name,'amount':float(amount),'method':payment.method,'date':payment.payment_date.isoformat(),'partyType':'customer'}},status=201)
    customer_rows=_company_qs(Payment,request).select_related('customer').order_by('-payment_date','-id')[:100]
    supplier_rows=_company_qs(SupplierPayment,request).select_related('supplier').order_by('-payment_date','-id')[:100]
    rows=[{'id':p.receipt_no,'party':p.customer.name,'amount':float(p.amount),'method':p.method,'date':p.payment_date.strftime('%d %b'),'partyType':'customer'} for p in customer_rows]+[{'id':p.payment_no,'party':p.supplier.name,'amount':float(p.amount),'method':p.method,'date':p.payment_date.strftime('%d %b'),'partyType':'supplier'} for p in supplier_rows]
    rows.sort(key=lambda x:x['date'],reverse=True)
    return JsonResponse({'payments':rows})


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','WAREHOUSE','ACCOUNTANT','SALES')
def warehouses(request):
    if request.method=='POST':
        if request.api_user.profile.role not in ['OWNER','MANAGER','WAREHOUSE']:
            return JsonResponse({'detail':'You have read-only access to warehouses.'},status=403)
        body=_json_body(request) or {}
        if body.get('kind')=='transfer':
            source=_company_qs(Warehouse,request).filter(pk=body.get('fromWarehouseId')).first(); target=_company_qs(Warehouse,request).filter(pk=body.get('toWarehouseId')).first(); items=body.get('items') or []
            if not source or not target or source==target or not items: return JsonResponse({'detail':'valid source, destination and items are required.'},status=400)
            transfer=StockTransfer.objects.create(company=request.company,transfer_no=body.get('transferNo') or _next_no('TR'),from_warehouse=source,to_warehouse=target,transfer_date=_date(body.get('date')),created_by=request.api_user)
            for row in items:
                product=_company_qs(Product,request).filter(pk=row.get('productId')).first()
                if product: StockTransferItem.objects.create(transfer=transfer,product=product,quantity=decimal(row.get('quantity')))
            audit(request,'create','StockTransfer',transfer.id,f'Created {transfer.transfer_no}')
            return JsonResponse({'transfer':_serialize_transfer(transfer)},status=201)
        if not body.get('code') or not body.get('name'): return JsonResponse({'detail':'code and name are required.'},status=400)
        warehouse=Warehouse.objects.create(company=request.company,branch=request.branch,code=body['code'],name=body['name'],city=body.get('city',''),address=body.get('address',''))
        audit(request,'create','Warehouse',warehouse.id,f'Created warehouse {warehouse.code}')
        return JsonResponse({'warehouse':_serialize_warehouse(warehouse)},status=201)
    locations=_company_qs(Warehouse,request).filter(is_active=True).order_by('name'); transfers=_company_qs(StockTransfer,request).select_related('from_warehouse','to_warehouse').prefetch_related('items').order_by('-transfer_date','-id')[:30]
    return JsonResponse({'warehouses':[_serialize_warehouse(w) for w in locations],'transfers':[_serialize_transfer(t) for t in transfers]})


def _serialize_warehouse(w):
    agg=w.stock_balances.aggregate(stock=Sum('quantity'),reserved=Sum('reserved'))
    return {'pk':w.id,'id':w.code,'name':w.name,'city':w.city,'stock':float(agg['stock'] or 0),'reserved':float(agg['reserved'] or 0)}


def _serialize_transfer(t):
    return {'pk':t.id,'id':t.transfer_no,'from':t.from_warehouse.name,'to':t.to_warehouse.name,'status':t.status,'date':t.transfer_date.strftime('%d %b'),'units':float(sum((i.quantity for i in t.items.all()),Decimal('0'))),'items':[{'productId':i.product_id,'quantity':float(i.quantity)} for i in t.items.all()]}


@csrf_exempt
@require_POST
@roles_allowed('OWNER','MANAGER','WAREHOUSE')
def transfer_action(request, pk):
    t=_company_qs(StockTransfer,request).select_related('from_warehouse','to_warehouse').prefetch_related('items__product').filter(pk=pk).first()
    if not t: return JsonResponse({'detail':'Transfer not found.'},status=404)
    action=(_json_body(request) or {}).get('action')
    try:
        with transaction.atomic():
            if action=='approve': t.status=StockTransfer.Status.APPROVED; t.approved_by=request.api_user; t.save(update_fields=['status','approved_by'])
            elif action=='dispatch':
                if t.status not in [StockTransfer.Status.APPROVED, StockTransfer.Status.IN_TRANSIT]:
                    return JsonResponse({'detail':'Transfer must be approved before dispatch.'},status=400)
                if t.status==StockTransfer.Status.IN_TRANSIT: return JsonResponse({'transfer':_serialize_transfer(t)})
                for item in t.items.all(): apply_stock(request.company,t.from_warehouse,item.product,-item.quantity,InventoryMovement.MovementType.TRANSFER_OUT,t.transfer_no,request.api_user,'Transfer dispatched')
                t.status=StockTransfer.Status.IN_TRANSIT; t.save(update_fields=['status'])
            elif action=='receive':
                if t.status!=StockTransfer.Status.IN_TRANSIT: return JsonResponse({'detail':'Transfer must be in transit before receiving.'},status=400)
                for item in t.items.all(): apply_stock(request.company,t.to_warehouse,item.product,item.quantity,InventoryMovement.MovementType.TRANSFER_IN,t.transfer_no,request.api_user,'Transfer received')
                t.status=StockTransfer.Status.RECEIVED; t.save(update_fields=['status'])
            elif action=='cancel': t.status=StockTransfer.Status.CANCELLED; t.save(update_fields=['status'])
            else: return JsonResponse({'detail':'Unknown transfer action.'},status=400)
    except ValueError as exc: return JsonResponse({'detail':str(exc)},status=400)
    audit(request,action,'StockTransfer',t.id,f'{action.title()} {t.transfer_no}')
    return JsonResponse({'transfer':_serialize_transfer(t)})


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','WAREHOUSE')
def barcode(request):
    if request.method=='POST':
        body=_json_body(request) or {}; code=str(body.get('code','')).strip(); product=_company_qs(Product,request).filter(Q(barcode=code)|Q(sku__iexact=code)).first()
        if not product: return JsonResponse({'detail':'Product not found.'},status=404)
        warehouse=_company_qs(Warehouse,request).filter(pk=body.get('warehouseId')).first() if body.get('warehouseId') else None
        action=body.get('action','Lookup'); qty=decimal(body.get('quantity',1))
        log=BarcodeScanLog.objects.create(product=product,warehouse=warehouse,action=action,quantity=qty,scanned_by=request.api_user)
        if action in ['Stock In','Stock Out']:
            if not warehouse: return JsonResponse({'detail':'Warehouse is required for stock changes.'},status=400)
            delta=qty if action=='Stock In' else -qty
            try: apply_stock(request.company,warehouse,product,delta,InventoryMovement.MovementType.ADJUSTMENT,f'SCAN-{log.id}',request.api_user,'Barcode stock action')
            except ValueError as exc: return JsonResponse({'detail':str(exc)},status=400)
        audit(request,'scan','Product',product.id,f'{action} scan for {product.sku}')
        return JsonResponse({'scan':{'id':log.id,'sku':product.sku,'name':product.name,'barcode':product.barcode or product.sku,'action':log.action,'quantity':float(log.quantity)}})
    rows=_company_qs(Product,request).filter(is_active=True).order_by('name')
    return JsonResponse({'barcodes':[{'id':p.id,'sku':p.sku,'name':p.name,'barcode':p.barcode or p.sku,'stock':float(p.stock),'unit':p.unit,'location':p.location} for p in rows]})


def _parse_whatsapp_items(raw_message, company):
    items=[]; lowered=raw_message.lower()
    for product in Product.objects.filter(company=company,is_active=True):
        tokens=[token for token in re.split(r'[^a-z0-9]+',product.name.lower()) if len(token)>2]
        sku_match=product.sku.lower() in lowered; required=min(2,len(tokens[:4])); name_match=(sum(1 for token in tokens[:4] if token in lowered)>=required) if required else False
        if not (sku_match or name_match): continue
        quantity=1; lines=[line for line in raw_message.splitlines() if product.sku.lower() in line.lower() or any(t in line.lower() for t in tokens[:2])]
        if lines:
            match=re.search(r'\b(\d+(?:\.\d+)?)\b',lines[0]); quantity=float(match.group(1)) if match else 1
        items.append({'productId':product.id,'sku':product.sku,'name':product.name,'quantity':quantity,'unit':product.unit,'price':float(product.sell_price),'available':float(product.stock)})
    return items


def _send_whatsapp_live(customer, message):
    token=os.getenv('WHATSAPP_ACCESS_TOKEN',''); phone_id=os.getenv('WHATSAPP_PHONE_NUMBER_ID','')
    if not token or not phone_id or not customer.phone: return None, 'Configured credentials are required for live WhatsApp delivery.'
    payload=json.dumps({'messaging_product':'whatsapp','to':customer.phone,'type':'text','text':{'body':message}}).encode()
    req=urllib.request.Request(f'https://graph.facebook.com/v21.0/{phone_id}/messages',data=payload,headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=8) as response: data=json.loads(response.read().decode()); return (data.get('messages') or [{}])[0].get('id'), None
    except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError) as exc: return None, str(exc)


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','SALES')
def whatsapp(request):
    if request.method=='POST':
        body=_json_body(request) or {}; customer=_company_qs(Customer,request).filter(pk=body.get('customerId')).first() or _company_qs(Customer,request).filter(code=body.get('customer')).first(); raw=str(body.get('message','')).strip(); direction=body.get('direction','Inbound')
        if not customer or not raw: return JsonResponse({'detail':'customer and message are required.'},status=400)
        if direction=='Outbound':
            provider_id,error=_send_whatsapp_live(customer,raw) if body.get('sendLive') else (None,None)
            status='Failed' if error else ('Sent' if provider_id else 'Demo')
            msg=WhatsAppMessage.objects.create(company=request.company,customer=customer,direction='Outbound',message=raw,status=status,provider_message_id=provider_id or '')
            audit(request,'send','WhatsAppMessage',msg.id,f'WhatsApp message to {customer.code}')
            return JsonResponse({'message':{'id':msg.id,'status':status,'providerId':provider_id,'error':error}},status=201)
        items=_parse_whatsapp_items(raw,request.company); total=sum(Decimal(str(x['quantity']))*Decimal(str(x['price'])) for x in items); draft=WhatsAppOrderDraft.objects.create(company=request.company,draft_no=_next_no('WA'),customer=customer,raw_message=raw,parsed_items=items,estimated_total=total); WhatsAppMessage.objects.create(company=request.company,customer=customer,direction='Inbound',message=raw,status='Received')
        audit(request,'create','WhatsAppOrderDraft',draft.id,f'Parsed WhatsApp order {draft.draft_no}')
        return JsonResponse({'draft':{'pk':draft.id,'id':draft.draft_no,'customer':customer.name,'items':items,'total':float(total),'status':draft.status}},status=201)
    drafts=_company_qs(WhatsAppOrderDraft,request).select_related('customer').order_by('-created_at')[:30]
    return JsonResponse({'whatsapp':[{'pk':d.id,'id':d.draft_no,'customer':d.customer.name,'message':d.raw_message,'items':d.parsed_items,'total':float(d.estimated_total),'status':d.status} for d in drafts],'integration':{'configured':bool(os.getenv('WHATSAPP_ACCESS_TOKEN') and os.getenv('WHATSAPP_PHONE_NUMBER_ID'))}})


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','SALES','ACCOUNTANT')
def tax_compliance(request):
    if request.method=='POST':
        body=_json_body(request) or {}; customer=_company_qs(Customer,request).filter(pk=body.get('customerId')).first(); invoice=_company_qs(Invoice,request).filter(pk=body.get('invoiceId')).first() if body.get('invoiceId') else None
        if not customer: return JsonResponse({'detail':'customer is required.'},status=400)
        note=TaxNote.objects.create(company=request.company,note_no=body.get('noteNo') or _next_no('CN' if body.get('type')=='Credit Note' else 'DN'),note_type=body.get('type','Credit Note'),customer=customer,invoice=invoice,taxable_amount=decimal(body.get('taxable')),gst_amount=decimal(body.get('gst')),total=decimal(body.get('total')),note_date=_date(body.get('date')),reason=body.get('reason',''))
        if note.note_type==TaxNote.NoteType.CREDIT:
            customer.outstanding=max(Decimal('0'),customer.outstanding-note.total); customer.save(update_fields=['outstanding']); LedgerEntry.objects.create(company=request.company,customer=customer,entry_type=LedgerEntry.EntryType.CREDIT_NOTE,reference=note.note_no,amount=-note.total,entry_date=note.note_date,note=note.reason)
        audit(request,'create','TaxNote',note.id,f'Created {note.note_no}')
        return JsonResponse({'note':{'id':note.note_no,'type':note.note_type,'total':float(note.total)}},status=201)
    invoices_qs=_company_qs(Invoice,request).select_related('order__customer').order_by('-invoice_date')[:50]; notes=_company_qs(TaxNote,request).select_related('customer','invoice').order_by('-note_date')[:30]
    return JsonResponse({'tax':{'invoices':[_serialize_invoice(i) for i in invoices_qs],'notes':[{'pk':n.id,'id':n.note_no,'type':n.note_type,'customer':n.customer.name,'invoice':n.invoice.invoice_no if n.invoice else '—','total':float(n.total),'date':n.note_date.strftime('%d %b'),'reason':n.reason} for n in notes],'integration':{'mode':'provider-ready','einvoice':bool(os.getenv('GST_PROVIDER_API_KEY')),'ewayBill':bool(os.getenv('GST_PROVIDER_API_KEY')),'message':'Configure GST_PROVIDER_API_KEY and your authorised provider adapter before live e-invoice/e-way-bill calls.'}}})


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','SALES')
def pricing(request):
    if request.method=='POST':
        body=_json_body(request) or {}; customer=_company_qs(Customer,request).filter(pk=body.get('customerId')).first() if body.get('customerId') else None
        price_list=PriceList.objects.create(company=request.company,name=body.get('name','New price list'),customer=customer,valid_from=_date(body.get('validFrom')) if body.get('validFrom') else None,valid_to=_date(body.get('validTo')) if body.get('validTo') else None)
        for row in body.get('rules',[]):
            product=_company_qs(Product,request).filter(pk=row.get('productId')).first()
            if product: PriceRule.objects.create(price_list=price_list,product=product,min_quantity=decimal(row.get('minQty',1)),price=decimal(row.get('price',product.sell_price)),discount_percent=decimal(row.get('discount',0)),scheme_text=row.get('scheme',''))
        audit(request,'create','PriceList',price_list.id,f'Created price list {price_list.name}')
        return JsonResponse({'id':price_list.id},status=201)
    lists=_company_qs(PriceList,request).filter(is_active=True).select_related('customer').prefetch_related('rules__product').order_by('name')
    return JsonResponse({'pricing':[{'id':pl.id,'name':pl.name,'customer':pl.customer.name if pl.customer else 'All dealer customers','validFrom':pl.valid_from.isoformat() if pl.valid_from else None,'validTo':pl.valid_to.isoformat() if pl.valid_to else None,'rules':[{'productId':r.product_id,'sku':r.product.sku,'product':r.product.name,'minQty':float(r.min_quantity),'price':float(r.price),'discount':float(r.discount_percent),'scheme':r.scheme_text} for r in pl.rules.all()]} for pl in lists]})


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','WAREHOUSE','ACCOUNTANT')
def returns_adjustments(request):
    if request.method=='POST':
        body=_json_body(request) or {}; kind=body.get('kind','return'); warehouse=_company_qs(Warehouse,request).filter(pk=body.get('warehouseId')).first()
        if not warehouse: return JsonResponse({'detail':'warehouse is required.'},status=400)
        if kind=='adjustment':
            product=_company_qs(Product,request).filter(pk=body.get('productId')).first(); qty=decimal(body.get('quantity'))
            if not product or qty==0: return JsonResponse({'detail':'product and non-zero quantity are required.'},status=400)
            adjustment=StockAdjustment.objects.create(company=request.company,adjustment_no=_next_no('ADJ'),product=product,warehouse=warehouse,adjustment_type=body.get('type','Other'),quantity=qty,reason=body.get('reason','Manual adjustment'),adjustment_date=_date(body.get('date')),created_by=request.api_user)
            try: apply_stock(request.company,warehouse,product,qty,InventoryMovement.MovementType.ADJUSTMENT,adjustment.adjustment_no,request.api_user,adjustment.reason)
            except ValueError as exc: adjustment.delete(); return JsonResponse({'detail':str(exc)},status=400)
            audit(request,'create','StockAdjustment',adjustment.id,f'Created {adjustment.adjustment_no}')
            return JsonResponse({'id':adjustment.adjustment_no},status=201)
        return_type=body.get('type','Sales Return'); customer=_company_qs(Customer,request).filter(pk=body.get('customerId')).first() if body.get('customerId') else None; supplier=_company_qs(Supplier,request).filter(pk=body.get('supplierId')).first() if body.get('supplierId') else None; items=body.get('items') or []
        if return_type=='Sales Return' and not customer: return JsonResponse({'detail':'customer is required for a sales return.'},status=400)
        if return_type=='Purchase Return' and not supplier: return JsonResponse({'detail':'supplier is required for a purchase return.'},status=400)
        ro=ReturnOrder.objects.create(company=request.company,return_no=_next_no('SR' if return_type=='Sales Return' else 'PR'),return_type=return_type,customer=customer,supplier=supplier,warehouse=warehouse,status=ReturnOrder.Status.COMPLETED,return_date=_date(body.get('date')),reason=body.get('reason',''),created_by=request.api_user)
        total=Decimal('0')
        try:
            with transaction.atomic():
                for row in items:
                    product=_company_qs(Product,request).get(pk=row.get('productId')); qty=decimal(row.get('quantity')); price=decimal(row.get('unitPrice',product.sell_price if return_type=='Sales Return' else product.purchase_price)); ReturnItem.objects.create(return_order=ro,product=product,quantity=qty,unit_price=price,condition=row.get('condition','Resellable')); total+=qty*price; delta=qty if return_type=='Sales Return' and row.get('condition','Resellable')=='Resellable' else (-qty if return_type=='Purchase Return' else Decimal('0'))
                    if delta: apply_stock(request.company,warehouse,product,delta,InventoryMovement.MovementType.SALES_RETURN if delta>0 else InventoryMovement.MovementType.PURCHASE_RETURN,ro.return_no,request.api_user,ro.reason)
                ro.total=total; ro.save(update_fields=['total'])
        except (Product.DoesNotExist,ValueError) as exc: ro.delete(); return JsonResponse({'detail':str(exc)},status=400)
        audit(request,'create','ReturnOrder',ro.id,f'Created {ro.return_no}')
        return JsonResponse({'id':ro.return_no,'total':float(total)},status=201)
    returns=_company_qs(ReturnOrder,request).select_related('customer','supplier','warehouse').prefetch_related('items').order_by('-return_date')[:50]; adjustments=_company_qs(StockAdjustment,request).select_related('product','warehouse').order_by('-adjustment_date')[:50]
    return JsonResponse({'returns':{'returns':[{'pk':r.id,'id':r.return_no,'type':r.return_type,'party':r.customer.name if r.customer else (r.supplier.name if r.supplier else '—'),'warehouse':r.warehouse.name,'items':r.items.count(),'total':float(r.total),'date':r.return_date.strftime('%d %b'),'status':r.status,'reason':r.reason} for r in returns],'adjustments':[{'pk':a.id,'id':a.adjustment_no,'type':a.adjustment_type,'product':a.product.name,'sku':a.product.sku,'warehouse':a.warehouse.name,'quantity':float(a.quantity),'date':a.adjustment_date.strftime('%d %b'),'reason':a.reason} for a in adjustments]}})


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','SALES')
def field_sales(request):
    if request.method=='POST':
        body=_json_body(request) or {}; customer=_company_qs(Customer,request).filter(pk=body.get('customerId')).first(); salesperson=request.api_user if request.api_user.profile.role=='SALES' else User.objects.filter(pk=body.get('salespersonId'),profile__company=request.company,profile__role='SALES').first()
        if not customer or not salesperson: return JsonResponse({'detail':'customer and salesperson are required.'},status=400)
        visit=SalesVisit.objects.create(company=request.company,salesperson=salesperson,customer=customer,visit_date=_date(body.get('date')),status=body.get('status','Planned'),territory=body.get('territory',''),order_value=decimal(body.get('orderValue')),collection_amount=decimal(body.get('collection')),notes=body.get('notes',''))
        audit(request,'create','SalesVisit',visit.id,f'Created visit for {customer.code}')
        return JsonResponse({'id':visit.id},status=201)
    user=request.api_user; visits=_company_qs(SalesVisit,request).select_related('salesperson','customer').order_by('-visit_date','customer__name');
    if user.profile.role=='SALES': visits=visits.filter(salesperson=user)
    target=_company_qs(SalesTarget,request).filter(salesperson=user).order_by('-month').first() if user.profile.role=='SALES' else _company_qs(SalesTarget,request).order_by('-month').first()
    return JsonResponse({'fieldSales':{'visits':[{'id':v.id,'salesperson':v.salesperson.get_full_name() or v.salesperson.username,'customer':v.customer.name,'city':v.customer.city,'date':v.visit_date.strftime('%d %b'),'status':v.status,'territory':v.territory,'orderValue':float(v.order_value),'collection':float(v.collection_amount),'notes':v.notes} for v in visits[:50]],'target':{'sales':float(target.target_sales),'collection':float(target.target_collection)} if target else {'sales':0,'collection':0}}})


@require_GET
@roles_allowed('OWNER','MANAGER','WAREHOUSE','ACCOUNTANT')
def insights(request):
    suggestions=ReorderSuggestion.objects.filter(product__company=request.company,warehouse__company=request.company).select_related('product','warehouse').order_by('risk','days_cover'); top_receivables=_company_qs(Customer,request).order_by('-outstanding')[:5]; products_qs=_company_qs(Product,request); total_stock_value=sum((p.stock*p.purchase_price for p in products_qs),Decimal('0')); month_sales=_company_qs(Order,request).aggregate(total=Sum('total'))['total'] or Decimal('0')
    return JsonResponse({'insights':{'metrics':{'sales':float(month_sales),'stockValue':float(total_stock_value),'receivable':float(_company_qs(Customer,request).aggregate(total=Sum('outstanding'))['total'] or 0),'highRisk':suggestions.filter(risk='High').count()},'reorder':[{'sku':s.product.sku,'product':s.product.name,'warehouse':s.warehouse.name,'stock':float(s.current_stock),'dailySales':float(s.avg_daily_sales),'leadTime':s.lead_time_days,'suggested':float(s.suggested_quantity),'daysCover':float(s.days_cover),'risk':s.risk} for s in suggestions],'receivables':[{'customer':c.name,'city':c.city,'outstanding':float(c.outstanding),'limit':float(c.credit_limit)} for c in top_receivables]}})


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','SALES')
def quotations(request):
    if request.method=='POST':
        body=_json_body(request) or {}; customer=_company_qs(Customer,request).filter(pk=body.get('customerId')).first(); warehouse=_company_qs(Warehouse,request).filter(pk=body.get('warehouseId')).first(); items=body.get('items') or []
        if not customer or not items: return JsonResponse({'detail':'customer and items are required.'},status=400)
        quote=Quotation.objects.create(company=request.company,quote_no=body.get('quoteNo') or _next_no('QT'),customer=customer,warehouse=warehouse,quote_date=_date(body.get('date')),valid_until=_date(body.get('validUntil')) if body.get('validUntil') else None,notes=body.get('notes',''),created_by=request.api_user); subtotal=tax=Decimal('0')
        for row in items:
            product=_company_qs(Product,request).filter(pk=row.get('productId')).first()
            if not product: continue
            line=calculate_line(product,row.get('quantity',1),row.get('unitPrice'),0,row.get('gstRate')); QuotationItem.objects.create(quotation=quote,product=product,quantity=line['quantity'],unit_price=line['unit_price'],gst_rate=line['gst_rate'],line_total=line['total']); subtotal+=line['taxable']; tax+=line['tax']
        quote.subtotal=subtotal; quote.tax=tax; quote.total=subtotal+tax; quote.save(update_fields=['subtotal','tax','total']); audit(request,'create','Quotation',quote.id,f'Created {quote.quote_no}')
        return JsonResponse({'quotation':_serialize_quote(quote)},status=201)
    rows=_company_qs(Quotation,request).select_related('customer','warehouse','converted_order').prefetch_related('items__product').order_by('-quote_date','-id')
    return JsonResponse({'quotations':[_serialize_quote(q) for q in rows]})


def _serialize_quote(q):
    return {'pk':q.id,'id':q.quote_no,'customer':q.customer.name,'customerId':q.customer_id,'date':q.quote_date.strftime('%d %b'),'validUntil':q.valid_until.isoformat() if q.valid_until else None,'status':q.status,'total':float(q.total),'warehouse':q.warehouse.name if q.warehouse else '—','order':q.converted_order.order_no if q.converted_order else None,'items':[{'productId':i.product_id,'product':i.product.name,'sku':i.product.sku,'quantity':float(i.quantity),'unitPrice':float(i.unit_price),'total':float(i.line_total)} for i in q.items.all()]}


@csrf_exempt
@require_POST
@roles_allowed('OWNER','MANAGER','SALES')
def quotation_action(request, pk):
    quote=_company_qs(Quotation,request).select_related('customer','warehouse').prefetch_related('items__product').filter(pk=pk).first()
    if not quote: return JsonResponse({'detail':'Quotation not found.'},status=404)
    action=(_json_body(request) or {}).get('action')
    if action in ['sent','accepted','rejected']:
        quote.status={'sent':Quotation.Status.SENT,'accepted':Quotation.Status.ACCEPTED,'rejected':Quotation.Status.REJECTED}[action]; quote.save(update_fields=['status']); audit(request,action,'Quotation',quote.id,f'{action.title()} {quote.quote_no}'); return JsonResponse({'quotation':_serialize_quote(quote)})
    if action=='convert':
        if quote.converted_order: return JsonResponse({'quotation':_serialize_quote(quote)})
        warehouse=quote.warehouse or _company_qs(Warehouse,request).filter(is_active=True).first()
        if not warehouse: return JsonResponse({'detail':'A warehouse is required before converting.'},status=400)
        order=Order.objects.create(company=request.company,branch=request.branch,warehouse=warehouse,order_no=_next_no('SO'),customer=quote.customer,order_date=timezone.localdate(),notes=f'Converted from {quote.quote_no}',created_by=request.api_user)
        create_order_items(order,[{'product_id':i.product_id,'quantity':i.quantity,'unit_price':i.unit_price,'gst_rate':i.gst_rate} for i in quote.items.all()]); quote.converted_order=order; quote.status=Quotation.Status.CONVERTED; quote.save(update_fields=['converted_order','status']); audit(request,'convert','Quotation',quote.id,f'Converted {quote.quote_no} to {order.order_no}'); return JsonResponse({'quotation':_serialize_quote(quote),'order':_serialize_order(order,True)})
    return JsonResponse({'detail':'Unknown quotation action.'},status=400)


@require_GET
@roles_allowed('OWNER','MANAGER','ACCOUNTANT')
def reports(request):
    today=timezone.localdate(); orders=_company_qs(Order,request); payments_qs=_company_qs(Payment,request); purchases_qs=_company_qs(PurchaseOrder,request); customers_qs=_company_qs(Customer,request); suppliers_qs=_company_qs(Supplier,request)
    sales_month=orders.filter(order_date__year=today.year,order_date__month=today.month).aggregate(v=Sum('total'))['v'] or 0; collected=payments_qs.filter(payment_date__year=today.year,payment_date__month=today.month).aggregate(v=Sum('amount'))['v'] or 0; purchases_total=purchases_qs.filter(order_date__year=today.year,order_date__month=today.month).aggregate(v=Sum('total'))['v'] or 0; receivable=customers_qs.aggregate(v=Sum('outstanding'))['v'] or 0; payable=suppliers_qs.aggregate(v=Sum('outstanding'))['v'] or 0; stock_value=sum((p.stock*p.purchase_price for p in _company_qs(Product,request)),Decimal('0'))
    top_customers=orders.values('customer__name').annotate(total=Sum('total')).order_by('-total')[:8]
    return JsonResponse({'reports':{'sales':float(sales_month),'collections':float(collected),'purchases':float(purchases_total),'receivable':float(receivable),'payable':float(payable),'stockValue':float(stock_value),'topCustomers':[{'name':x['customer__name'],'sales':float(x['total'])} for x in top_customers]}})


@require_GET
@roles_allowed('OWNER','MANAGER','ACCOUNTANT')
def export_csv(request, resource):
    output=io.StringIO(); writer=csv.writer(output)
    if resource=='products':
        writer.writerow(['SKU','Name','Category','Stock','Unit','Purchase Price','Sell Price','Reorder','HSN','GST Rate']);
        for p in _company_qs(Product,request).order_by('name'): writer.writerow([p.sku,p.name,p.category,p.stock,p.unit,p.purchase_price,p.sell_price,p.reorder_level,p.hsn_code,p.gst_rate])
    elif resource=='customers':
        writer.writerow(['Code','Name','City','State','Phone','Email','GSTIN','Outstanding','Credit Limit']);
        for c in _company_qs(Customer,request).order_by('name'): writer.writerow([c.code,c.name,c.city,c.state,c.phone,c.email,c.gstin,c.outstanding,c.credit_limit])
    elif resource=='ledger':
        writer.writerow(['Date','Customer','Type','Reference','Amount','Due']);
        for x in _company_qs(LedgerEntry,request).select_related('customer').order_by('-entry_date'): writer.writerow([x.entry_date,x.customer.name,x.entry_type,x.reference,x.amount,x.due_date or ''])
    elif resource=='orders':
        writer.writerow(['Order','Date','Customer','Status','Payment','Total']);
        for o in _company_qs(Order,request).select_related('customer').order_by('-order_date'): writer.writerow([o.order_no,o.order_date,o.customer.name,o.status,o.payment_status,o.total])
    else: return JsonResponse({'detail':'Unsupported export resource.'},status=404)
    response=HttpResponse(output.getvalue(),content_type='text/csv'); response['Content-Disposition']=f'attachment; filename="setustock-{resource}-{timezone.localdate()}.csv"'; return response


@csrf_exempt
@require_POST
@roles_allowed('OWNER','MANAGER')
def import_csv(request, resource):
    upload=request.FILES.get('file')
    if not upload: return JsonResponse({'detail':'CSV file is required.'},status=400)
    if upload.size>5*1024*1024: return JsonResponse({'detail':'CSV must be 5 MB or smaller.'},status=400)
    try: text=upload.read().decode('utf-8-sig'); rows=list(csv.DictReader(io.StringIO(text)))
    except Exception: return JsonResponse({'detail':'Could not parse CSV.'},status=400)
    created=updated=0
    if resource=='products':
        for row in rows:
            sku=(row.get('SKU') or row.get('sku') or '').strip(); name=(row.get('Name') or row.get('name') or '').strip()
            if not sku or not name: continue
            _,made=Product.objects.update_or_create(company=request.company,sku=sku,defaults={'name':name,'category':row.get('Category',''),'unit':row.get('Unit','pcs'),'purchase_price':decimal(row.get('Purchase Price',0)),'sell_price':decimal(row.get('Sell Price',0)),'reorder_level':decimal(row.get('Reorder',0)),'hsn_code':row.get('HSN',''),'gst_rate':decimal(row.get('GST Rate',18))}); created+=int(made); updated+=int(not made)
    elif resource=='customers':
        for row in rows:
            code=(row.get('Code') or row.get('code') or '').strip(); name=(row.get('Name') or row.get('name') or '').strip()
            if not code or not name: continue
            _,made=Customer.objects.update_or_create(company=request.company,code=code,defaults={'name':name,'city':row.get('City',''),'state':row.get('State',request.company.state),'phone':row.get('Phone',''),'email':row.get('Email',''),'gstin':row.get('GSTIN',''),'credit_limit':decimal(row.get('Credit Limit',0))}); created+=int(made); updated+=int(not made)
    else: return JsonResponse({'detail':'Unsupported import resource.'},status=404)
    audit(request,'import',resource,'bulk',f'Imported {resource}',{'created':created,'updated':updated})
    return JsonResponse({'created':created,'updated':updated,'rows':len(rows)})


@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER')
def team(request):
    if request.method=='POST':
        body=_json_body(request) or {}; email=str(body.get('email','')).strip().lower(); role=body.get('role','SALES'); name=str(body.get('name','')).strip()
        if not email or role not in PERMISSIONS: return JsonResponse({'detail':'valid email and role are required.'},status=400)
        if User.objects.filter(email__iexact=email).exists(): return JsonResponse({'detail':'An account with this email already exists.'},status=400)
        username=f"u_{request.company.id}_{email.split('@')[0]}"[:140]; base=username; n=1
        while User.objects.filter(username=username).exists(): n+=1; username=f'{base}_{n}'
        parts=name.split(' ',1); user=User.objects.create_user(username=username,email=email,password=body.get('temporaryPassword') or 'ChangeMe123!',first_name=parts[0] if parts else '',last_name=parts[1] if len(parts)>1 else '')
        from .models import Profile
        Profile.objects.create(user=user,role=role,business_name=request.company.name,company=request.company,branch=request.branch,phone=body.get('phone',''))
        audit(request,'invite','User',user.id,f'Created team account {email}',{'role':role})
        return JsonResponse({'user':user_payload(user),'temporaryPassword':body.get('temporaryPassword') or 'ChangeMe123!'},status=201)
    users=User.objects.filter(profile__company=request.company).select_related('profile__branch').order_by('first_name','username')
    return JsonResponse({'team':[{'id':u.id,'name':u.get_full_name() or u.username,'email':u.email,'role':u.profile.role,'branch':u.profile.branch.name if u.profile.branch else 'All branches','active':u.is_active,'lastLogin':u.last_login.isoformat() if u.last_login else None} for u in users]})


@csrf_exempt
@require_http_methods(['PATCH'])
@roles_allowed('OWNER')
def team_member(request, pk):
    user=User.objects.filter(pk=pk,profile__company=request.company).select_related('profile').first()
    if not user: return JsonResponse({'detail':'Team member not found.'},status=404)
    if user==request.api_user and (_json_body(request) or {}).get('active') is False: return JsonResponse({'detail':'You cannot deactivate your own account.'},status=400)
    body=_json_body(request) or {}
    if 'role' in body and body['role'] in PERMISSIONS: user.profile.role=body['role']; user.profile.save(update_fields=['role'])
    if 'active' in body: user.is_active=bool(body['active']); user.save(update_fields=['is_active'])
    audit(request,'update','User',user.id,f'Updated team member {user.email}',body)
    return JsonResponse({'user':user_payload(user)})


@csrf_exempt
@require_http_methods(['GET','PATCH'])
@roles_allowed('OWNER','MANAGER')
def settings_view(request):
    c=request.company
    if request.method=='PATCH':
        body=_json_body(request) or {}; allowed=['name','gstin','pan','state','address','phone','email','bank_name','bank_account','ifsc','upi_id','logo_url','invoice_prefix','financial_year_start']
        for key in allowed:
            if key in body: setattr(c,key,body[key])
        c.save();
        from .models import Profile
        Profile.objects.filter(company=c).update(business_name=c.name)
        audit(request,'update','Company',c.id,'Updated company settings',body)
    branches=[{'id':b.id,'code':b.code,'name':b.name,'city':b.city,'gstin':b.gstin,'phone':b.phone} for b in c.branches.filter(is_active=True)]
    return JsonResponse({'settings':{'id':c.id,'name':c.name,'slug':c.slug,'gstin':c.gstin,'pan':c.pan,'state':c.state,'address':c.address,'phone':c.phone,'email':c.email,'bank_name':c.bank_name,'bank_account':c.bank_account,'ifsc':c.ifsc,'upi_id':c.upi_id,'logo_url':c.logo_url,'invoice_prefix':c.invoice_prefix,'financial_year_start':c.financial_year_start,'branches':branches,'demoMode':os.getenv('SETUSTOCK_DEMO_MODE','false').lower()=='true'}})


@csrf_exempt
@require_POST
@roles_allowed('OWNER')
def branches(request):
    body=_json_body(request) or {}
    if not body.get('code') or not body.get('name'): return JsonResponse({'detail':'code and name are required.'},status=400)
    branch=Branch.objects.create(company=request.company,code=body['code'],name=body['name'],city=body.get('city',''),address=body.get('address',''),gstin=body.get('gstin',''),phone=body.get('phone',''))
    audit(request,'create','Branch',branch.id,f'Created branch {branch.code}')
    return JsonResponse({'branch':{'id':branch.id,'code':branch.code,'name':branch.name}},status=201)


@require_GET
@api_auth_required
def global_search(request):
    q=request.GET.get('q','').strip()
    if len(q)<2: return JsonResponse({'results':[]})
    results=[]
    for p in _company_qs(Product,request).filter(Q(name__icontains=q)|Q(sku__icontains=q))[:8]: results.append({'type':'Product','id':p.id,'label':p.name,'meta':p.sku,'module':'products'})
    for c in _company_qs(Customer,request).filter(Q(name__icontains=q)|Q(code__icontains=q)|Q(phone__icontains=q))[:8]: results.append({'type':'Customer','id':c.id,'label':c.name,'meta':c.code,'module':'customers'})
    for o in _company_qs(Order,request).filter(Q(order_no__icontains=q)|Q(customer__name__icontains=q)).select_related('customer')[:8]: results.append({'type':'Order','id':o.id,'label':o.order_no,'meta':o.customer.name,'module':'orders'})
    for i in _company_qs(Invoice,request).filter(Q(invoice_no__icontains=q)|Q(order__customer__name__icontains=q)).select_related('order__customer')[:8]: results.append({'type':'Invoice','id':i.id,'label':i.invoice_no,'meta':i.order.customer.name,'module':'invoices'})
    return JsonResponse({'results':results[:20]})


@require_GET
@roles_allowed('OWNER','MANAGER','ACCOUNTANT')
def audit_logs(request):
    rows=AuditLog.objects.filter(company=request.company).select_related('actor').order_by('-created_at')[:200]
    return JsonResponse({'audit':[{'id':x.id,'action':x.action,'entity':x.entity_type,'entityId':x.entity_id,'summary':x.summary,'actor':(x.actor.get_full_name() or x.actor.username) if x.actor else 'System','time':x.created_at.isoformat(),'changes':x.changes} for x in rows]})


@csrf_exempt
@require_http_methods(['GET','PATCH'])
@api_auth_required
def notifications(request):
    qs=Notification.objects.filter(company=request.company).filter(Q(user=request.api_user)|Q(user__isnull=True))
    if request.method=='PATCH':
        body=_json_body(request) or {}
        if body.get('all'): qs.update(is_read=True)
        elif body.get('id'): qs.filter(pk=body['id']).update(is_read=True)
    rows=qs.order_by('-created_at')[:50]
    return JsonResponse({'notifications':[{'id':n.id,'title':n.title,'message':n.message,'level':n.level,'module':n.module,'entityId':n.entity_id,'read':n.is_read,'time':n.created_at.isoformat()} for n in rows],'unread':qs.filter(is_read=False).count()})


@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def attachments(request):
    if request.method=='POST':
        file=request.FILES.get('file'); module=request.POST.get('module',''); entity_id=request.POST.get('entityId','')
        if not file or not module or not entity_id: return JsonResponse({'detail':'file, module and entityId are required.'},status=400)
        max_size=int(os.getenv('ATTACHMENT_MAX_MB','10'))*1024*1024
        if file.size>max_size: return JsonResponse({'detail':f'File exceeds {os.getenv("ATTACHMENT_MAX_MB","10")} MB limit.'},status=400)
        allowed={'application/pdf','image/jpeg','image/png','text/csv','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}
        if file.content_type not in allowed: return JsonResponse({'detail':'File type is not allowed.'},status=400)
        a=Attachment.objects.create(company=request.company,module=module,entity_id=entity_id,file=file,original_name=file.name,content_type=file.content_type,size=file.size,uploaded_by=request.api_user); audit(request,'upload','Attachment',a.id,f'Uploaded {a.original_name}')
        return JsonResponse({'attachment':{'id':a.id,'name':a.original_name,'url':a.file.url,'size':a.size}},status=201)
    module=request.GET.get('module',''); entity_id=request.GET.get('entityId',''); qs=Attachment.objects.filter(company=request.company)
    if module: qs=qs.filter(module=module)
    if entity_id: qs=qs.filter(entity_id=entity_id)
    return JsonResponse({'attachments':[{'id':a.id,'name':a.original_name,'url':a.file.url,'size':a.size,'module':a.module,'entityId':a.entity_id,'time':a.created_at.isoformat()} for a in qs.order_by('-created_at')[:100]]})

@csrf_exempt
@require_POST
def portal_login(request):
    body = _json_body(request) or {}
    email = str(body.get('email', '')).strip().lower()
    pin = str(body.get('pin', ''))
    access = CustomerPortalAccess.objects.select_related('customer', 'company').filter(email__iexact=email, is_active=True).first()
    if not access or not check_password(pin, access.pin_hash):
        return JsonResponse({'detail': 'Invalid portal email or PIN.'}, status=401)
    access.last_login_at = timezone.now(); access.save(update_fields=['last_login_at'])
    return JsonResponse({'token': create_portal_token(access), 'customer': {'id': access.customer_id, 'name': access.customer.name, 'outstanding': float(access.customer.outstanding), 'creditLimit': float(access.customer.credit_limit)}, 'business': access.company.name})

@require_GET
@portal_auth_required
def portal_catalog(request):
    products_qs = Product.objects.filter(company=request.company, is_active=True).order_by('name')[:200]
    rows = []
    for p in products_qs:
        best = PriceRule.objects.filter(price_list__company=request.company, price_list__is_active=True, product=p).filter(Q(price_list__customer=request.customer) | Q(price_list__customer__isnull=True)).order_by('-min_quantity').first()
        rows.append({'id': p.id, 'sku': p.sku, 'name': p.name, 'stock': float(p.stock), 'unit': p.unit, 'price': float(best.price if best else p.sell_price), 'gst': float(p.gst_rate), 'image': p.image_url})
    recent = CustomerPortalOrder.objects.filter(company=request.company, customer=request.customer).order_by('-created_at')[:10]
    return JsonResponse({'products': rows, 'credit': {'outstanding': float(request.customer.outstanding), 'limit': float(request.customer.credit_limit)}, 'orders': [{'id': x.request_no, 'status': x.status, 'total': float(x.estimated_total), 'createdAt': x.created_at.isoformat()} for x in recent]})

@csrf_exempt
@require_POST
@portal_auth_required
def portal_place_order(request):
    body = _json_body(request) or {}
    items = body.get('items') or []
    if not isinstance(items, list) or not items:
        return JsonResponse({'detail': 'At least one cart item is required.'}, status=400)
    clean=[]; total=Decimal('0')
    for row in items[:100]:
        try: product=Product.objects.get(pk=int(row.get('productId')), company=request.company, is_active=True); qty=decimal(row.get('quantity'), '0')
        except (Product.DoesNotExist, TypeError, ValueError): continue
        if qty <= 0: continue
        price=product.sell_price; line=qty*price; total += line
        clean.append({'productId': product.id, 'sku': product.sku, 'name': product.name, 'quantity': float(qty), 'unit': product.unit, 'price': float(price), 'lineTotal': float(line)})
    if not clean: return JsonResponse({'detail': 'No valid cart items were supplied.'}, status=400)
    req=CustomerPortalOrder.objects.create(company=request.company, customer=request.customer, request_no=_next_no('WEB'), items=clean, estimated_total=total, notes=str(body.get('notes',''))[:1000])
    audit(request, 'create', req, f'Customer portal order {req.request_no} submitted', {'total': float(total)})
    return JsonResponse({'ok': True, 'requestNo': req.request_no, 'status': req.status, 'total': float(total)}, status=201)

@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','WAREHOUSE','SALES')
def delivery(request):
    if request.method=='POST':
        body=_json_body(request) or {}; action=body.get('action','create-run')
        if action=='create-run':
            run=DeliveryRun.objects.create(company=request.company,run_no=_next_no('RUN'),route_name=str(body.get('routeName','Delhi NCR Route'))[:120],driver_name=str(body.get('driverName',''))[:120],driver_phone=str(body.get('driverPhone',''))[:20],vehicle_no=str(body.get('vehicleNo',''))[:30],delivery_date=_date(body.get('deliveryDate')),created_by=request.api_user)
            for idx,oid in enumerate(body.get('orderIds') or [],1):
                order=Order.objects.filter(pk=oid,company=request.company).first()
                if order: DeliveryStop.objects.create(run=run,order=order,sequence=idx,cod_amount=order.total if order.payment_status!=Order.PaymentStatus.PAID else 0)
            audit(request,'create',run,f'Created delivery run {run.run_no}',{'route':run.route_name})
            return JsonResponse({'ok':True,'id':run.id,'runNo':run.run_no},status=201)
        stop=DeliveryStop.objects.select_related('run','order').filter(pk=body.get('stopId'),run__company=request.company).first()
        if not stop:return JsonResponse({'detail':'Delivery stop not found.'},status=404)
        if action=='deliver':
            stop.status=DeliveryStop.Status.DELIVERED;stop.delivered_at=timezone.now();stop.save(update_fields=['status','delivered_at'])
            DeliveryProof.objects.update_or_create(stop=stop,defaults={'otp_verified':bool(body.get('otpVerified',True)),'receiver_name':str(body.get('receiverName',''))[:120],'photo_url':str(body.get('photoUrl',''))[:200],'signature_data':str(body.get('signature',''))[:5000],'note':str(body.get('note',''))[:240]})
        elif action=='fail': stop.status=DeliveryStop.Status.FAILED;stop.failure_reason=str(body.get('reason','Unable to deliver'))[:240];stop.save(update_fields=['status','failure_reason'])
        return JsonResponse({'ok':True,'status':stop.status})
    runs=DeliveryRun.objects.filter(company=request.company).prefetch_related('stops__order__customer').order_by('-delivery_date','-id')[:30]
    return JsonResponse({'runs':[{'id':r.id,'runNo':r.run_no,'route':r.route_name,'driver':r.driver_name,'vehicle':r.vehicle_no,'date':r.delivery_date.isoformat(),'status':r.status,'stops':[{'id':s.id,'order':s.order.order_no,'customer':s.order.customer.name,'status':s.status,'cod':float(s.cod_amount),'sequence':s.sequence} for s in r.stops.all()]} for r in runs]})

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def approvals(request):
    if request.method=='POST':
        body=_json_body(request) or {}; action=body.get('action','request')
        if action=='request':
            policy=ApprovalPolicy.objects.filter(company=request.company,key=body.get('policyKey'),is_active=True).first()
            row=ApprovalRequest.objects.create(company=request.company,policy=policy,request_no=_next_no('APR'),entity_type=str(body.get('entityType','Manual'))[:60],entity_id=str(body.get('entityId',''))[:80],title=str(body.get('title','Approval required'))[:180],amount=decimal(body.get('amount')),payload=body.get('payload') if isinstance(body.get('payload'),dict) else {},requested_by=request.api_user)
            return JsonResponse({'ok':True,'id':row.id,'requestNo':row.request_no},status=201)
        row=ApprovalRequest.objects.filter(pk=body.get('id'),company=request.company,status=ApprovalRequest.Status.PENDING).first()
        if not row:return JsonResponse({'detail':'Pending approval not found.'},status=404)
        role=request.api_user.profile.role; expected=row.policy.approver_role if row.policy else 'MANAGER'
        if role not in ('OWNER',expected):return JsonResponse({'detail':f'{expected} approval required.'},status=403)
        row.status=ApprovalRequest.Status.APPROVED if action=='approve' else ApprovalRequest.Status.REJECTED;row.decided_by=request.api_user;row.decision_note=str(body.get('note',''))[:240];row.decided_at=timezone.now();row.save(update_fields=['status','decided_by','decision_note','decided_at'])
        audit(request,action,row,f'{action.title()}d {row.request_no}',{'entity':row.entity_type})
        return JsonResponse({'ok':True,'status':row.status})
    policies=ApprovalPolicy.objects.filter(company=request.company).order_by('label'); rows=ApprovalRequest.objects.filter(company=request.company).select_related('requested_by','decided_by','policy').order_by('-created_at')[:100]
    return JsonResponse({'policies':[{'key':p.key,'label':p.label,'threshold':float(p.threshold),'approverRole':p.approver_role,'active':p.is_active} for p in policies],'requests':[{'id':r.id,'requestNo':r.request_no,'title':r.title,'entity':r.entity_type,'amount':float(r.amount),'status':r.status,'requestedBy':r.requested_by.get_full_name() or r.requested_by.username if r.requested_by else 'System','approverRole':r.policy.approver_role if r.policy else 'MANAGER','createdAt':r.created_at.isoformat()} for r in rows]})

def _extract_invoice_text(raw):
    raw=raw or ''
    gst=re.search(r'\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b',raw.upper())
    inv=re.search(r'(?:invoice\s*(?:no|number)?\s*[:#-]?\s*)([A-Z0-9\-/]+)',raw,re.I)
    total_matches=re.findall(r'(?:grand\s+total|invoice\s+total|total)\s*[:₹Rs.]*\s*([\d,]+(?:\.\d{1,2})?)',raw,re.I)
    date_match=re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',raw)
    return {'invoiceNumber':inv.group(1) if inv else '', 'gstin':gst.group(0) if gst else '', 'invoiceDate':date_match.group(1) if date_match else '', 'total':float(total_matches[-1].replace(',','')) if total_matches else 0, 'lineItems':[]}

@csrf_exempt
@require_http_methods(['GET','POST','PATCH'])
@roles_allowed('OWNER','MANAGER','ACCOUNTANT','WAREHOUSE')
def invoice_ocr(request):
    if request.method=='POST':
        body=_json_body(request) or {}; raw=str(body.get('rawText',''))[:30000]; data=_extract_invoice_text(raw)
        supplier=Supplier.objects.filter(company=request.company,gstin=data.get('gstin')).first() if data.get('gstin') else None
        cap=PurchaseInvoiceCapture.objects.create(company=request.company,supplier=supplier,file_name=str(body.get('fileName','supplier-invoice.pdf'))[:200],file_url=str(body.get('fileUrl',''))[:200],raw_text=raw,extracted_data=data,confidence=Decimal('88.00') if data.get('invoiceNumber') and data.get('total') else Decimal('62.00'),status=PurchaseInvoiceCapture.Status.EXTRACTED,created_by=request.api_user)
        return JsonResponse({'capture':{'id':cap.id,'status':cap.status,'confidence':float(cap.confidence),'data':cap.extracted_data}},status=201)
    if request.method=='PATCH':
        body=_json_body(request) or {}; cap=PurchaseInvoiceCapture.objects.filter(pk=body.get('id'),company=request.company).first()
        if not cap:return JsonResponse({'detail':'Capture not found.'},status=404)
        if isinstance(body.get('data'),dict):cap.extracted_data=body['data']
        cap.status=body.get('status',PurchaseInvoiceCapture.Status.REVIEWED);cap.save(update_fields=['extracted_data','status','updated_at'])
        return JsonResponse({'ok':True,'status':cap.status})
    rows=PurchaseInvoiceCapture.objects.filter(company=request.company).select_related('supplier').order_by('-created_at')[:50]
    return JsonResponse({'captures':[{'id':x.id,'fileName':x.file_name,'supplier':x.supplier.name if x.supplier else 'Unmatched supplier','status':x.status,'confidence':float(x.confidence),'data':x.extracted_data,'createdAt':x.created_at.isoformat()} for x in rows]})

def _accounting_vouchers(company, start, end):
    rows=[]
    for inv in Invoice.objects.filter(company=company, invoice_date__range=(start,end)).select_related('order__customer'):
        rows.append({'type':'Sales','date':inv.invoice_date.isoformat(),'reference':inv.invoice_no,'party':inv.order.customer.name,'amount':float(inv.total),'gst':float(inv.cgst+inv.sgst+inv.igst)})
    for pay in Payment.objects.filter(company=company,payment_date__range=(start,end)).select_related('customer'):
        rows.append({'type':'Receipt','date':pay.payment_date.isoformat(),'reference':pay.receipt_no,'party':pay.customer.name,'amount':float(pay.amount),'method':pay.method})
    for po in PurchaseOrder.objects.filter(company=company,order_date__range=(start,end)).select_related('supplier'):
        rows.append({'type':'Purchase','date':po.order_date.isoformat(),'reference':po.po_no,'party':po.supplier.name,'amount':float(po.total)})
    for pay in SupplierPayment.objects.filter(company=company,payment_date__range=(start,end)).select_related('supplier'):
        rows.append({'type':'Payment','date':pay.payment_date.isoformat(),'reference':pay.payment_no,'party':pay.supplier.name,'amount':float(pay.amount),'method':pay.method})
    return rows

@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','ACCOUNTANT')
def accounting(request):
    conn,_=AccountingConnection.objects.get_or_create(company=request.company,defaults={'provider':'CSV'})
    if request.method=='POST':
        body=_json_body(request) or {}; action=body.get('action','export')
        if action=='configure':
            conn.provider=body.get('provider','CSV') if body.get('provider') in dict(AccountingConnection.Provider.choices) else 'CSV'; conn.is_active=bool(body.get('active')); conn.settings=body.get('settings') if isinstance(body.get('settings'),dict) else {}; conn.save(); return JsonResponse({'ok':True})
        start=_date(body.get('from'),timezone.localdate().replace(day=1));end=_date(body.get('to'),timezone.localdate());payload=_accounting_vouchers(request.company,start,end)
        job=AccountingExportJob.objects.create(company=request.company,provider=conn.provider,export_no=_next_no('ACC'),period_from=start,period_to=end,voucher_count=len(payload),payload=payload,status=AccountingExportJob.Status.READY,created_by=request.api_user)
        return JsonResponse({'job':{'id':job.id,'exportNo':job.export_no,'voucherCount':job.voucher_count,'status':job.status,'payload':payload}},status=201)
    jobs=AccountingExportJob.objects.filter(company=request.company).order_by('-created_at')[:20]
    return JsonResponse({'connection':{'provider':conn.provider,'active':conn.is_active,'lastSyncAt':conn.last_sync_at.isoformat() if conn.last_sync_at else None},'jobs':[{'id':j.id,'exportNo':j.export_no,'provider':j.provider,'from':j.period_from.isoformat(),'to':j.period_to.isoformat(),'voucherCount':j.voucher_count,'status':j.status,'createdAt':j.created_at.isoformat()} for j in jobs]})

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def offline_sync(request):
    if request.method=='GET':
        recent=OfflineSyncReceipt.objects.filter(company=request.company,user=request.api_user).order_by('-synced_at')[:20]
        return JsonResponse({'online':True,'recent':[{'eventId':x.event_id,'type':x.event_type,'syncedAt':x.synced_at.isoformat()} for x in recent]})
    body=_json_body(request) or {}; events=body.get('events') or []; device=str(body.get('deviceId',''))[:100]; results=[]
    if not isinstance(events,list):return JsonResponse({'detail':'events must be a list.'},status=400)
    for event in events[:100]:
        if not isinstance(event,dict):continue
        event_id=str(event.get('id',''))[:80]; kind=str(event.get('type',''))[:50]; payload=event.get('payload') if isinstance(event.get('payload'),dict) else {}
        if not event_id or not kind:continue
        receipt,created=OfflineSyncReceipt.objects.get_or_create(company=request.company,event_id=event_id,defaults={'event_type':kind,'payload':payload,'device_id':device,'user':request.api_user})
        if created and kind=='sales-visit':
            customer=Customer.objects.filter(pk=payload.get('customerId'),company=request.company).first()
            if customer: SalesVisit.objects.create(company=request.company,salesperson=request.api_user,customer=customer,visit_date=_date(payload.get('date')),status=payload.get('status','Visited'),territory=str(payload.get('territory',''))[:100],order_value=decimal(payload.get('orderValue')),collection_amount=decimal(payload.get('collection')),notes=str(payload.get('notes',''))[:240])
        results.append({'id':event_id,'status':'synced' if created else 'duplicate'})
    return JsonResponse({'ok':True,'results':results,'synced':len(results)})

@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER')
def subscription_billing(request):
    # Ensure a useful baseline exists even on a fresh tenant database.
    starter,_=SubscriptionPlan.objects.get_or_create(code='STARTER',defaults={'name':'Starter','monthly_price':999,'annual_price':9990,'user_limit':3,'branch_limit':1,'warehouse_limit':1,'features':['Core ERP','GST invoices','Customer portal']})
    growth,_=SubscriptionPlan.objects.get_or_create(code='GROWTH',defaults={'name':'Growth','monthly_price':2499,'annual_price':24990,'user_limit':10,'branch_limit':3,'warehouse_limit':5,'features':['Everything in Starter','WhatsApp','Field sales','Approvals','Delivery']})
    business,_=SubscriptionPlan.objects.get_or_create(code='BUSINESS',defaults={'name':'Business','monthly_price':4999,'annual_price':49990,'user_limit':50,'branch_limit':20,'warehouse_limit':50,'features':['Everything in Growth','Accounting','AI assistant','Advanced forecasting']})
    sub=CompanySubscription.objects.filter(company=request.company).select_related('plan').first()
    if not sub: sub=CompanySubscription.objects.create(company=request.company,plan=growth,status=CompanySubscription.Status.TRIAL,started_at=timezone.localdate(),current_period_end=timezone.localdate()+timedelta(days=14),trial_end=timezone.localdate()+timedelta(days=14))
    if request.method=='POST':
        body=_json_body(request) or {}; action=body.get('action','change-plan')
        if action=='change-plan':
            plan=SubscriptionPlan.objects.filter(code=body.get('planCode'),is_active=True).first()
            if not plan:return JsonResponse({'detail':'Plan not found.'},status=404)
            sub.plan=plan;sub.status=CompanySubscription.Status.ACTIVE;sub.current_period_end=timezone.localdate()+timedelta(days=30);sub.save(update_fields=['plan','status','current_period_end','updated_at'])
            inv=SubscriptionInvoice.objects.create(company=request.company,subscription=sub,invoice_no=_next_no('SUB'),amount=plan.monthly_price,tax=plan.monthly_price*Decimal('0.18'),due_date=timezone.localdate()+timedelta(days=7))
            return JsonResponse({'ok':True,'invoiceNo':inv.invoice_no,'status':sub.status})
        if action=='cancel': sub.cancel_at_period_end=True;sub.save(update_fields=['cancel_at_period_end','updated_at']);return JsonResponse({'ok':True})
    plans=SubscriptionPlan.objects.filter(is_active=True).order_by('monthly_price'); invoices=SubscriptionInvoice.objects.filter(company=request.company).order_by('-created_at')[:20]
    return JsonResponse({'subscription':{'status':sub.status,'plan':sub.plan.code,'planName':sub.plan.name,'periodEnd':sub.current_period_end.isoformat(),'cancelAtPeriodEnd':sub.cancel_at_period_end},'usage':{'users':request.company.profiles.count(),'branches':request.company.branches.count(),'warehouses':request.company.warehouses.count()},'plans':[{'code':p.code,'name':p.name,'monthly':float(p.monthly_price),'annual':float(p.annual_price),'userLimit':p.user_limit,'branchLimit':p.branch_limit,'warehouseLimit':p.warehouse_limit,'features':p.features} for p in plans],'invoices':[{'invoiceNo':x.invoice_no,'amount':float(x.amount+x.tax),'status':x.status,'dueDate':x.due_date.isoformat()} for x in invoices]})

def _forecast_row(company, product, warehouse=None, horizon=30):
    today=timezone.localdate(); recent_start=today-timedelta(days=30); prev_start=today-timedelta(days=60)
    base=OrderItem.objects.filter(order__company=company,product=product,order__status__in=[Order.Status.CONFIRMED,Order.Status.PROCESSING,Order.Status.PACKED,Order.Status.READY,Order.Status.DISPATCHED])
    if warehouse: base=base.filter(order__warehouse=warehouse)
    recent=base.filter(order__order_date__gte=recent_start).aggregate(q=Sum('quantity'))['q'] or Decimal('0'); prev=base.filter(order__order_date__gte=prev_start,order__order_date__lt=recent_start).aggregate(q=Sum('quantity'))['q'] or Decimal('0')
    avg=recent/Decimal('30'); trend=((recent-prev)/prev*100) if prev>0 else (Decimal('25') if recent>0 else Decimal('0')); multiplier=max(Decimal('0.5'),Decimal('1')+(trend/Decimal('100'))*Decimal('0.35')); forecast=avg*Decimal(str(horizon))*multiplier; safety=max(product.reorder_level,avg*Decimal('7')); current=product.stock
    if warehouse:
        bal=StockBalance.objects.filter(company=company,product=product,warehouse=warehouse).first(); current=bal.quantity if bal else Decimal('0')
    recommend=max(Decimal('0'),forecast+safety-current); confidence=Decimal('82') if recent>0 and prev>0 else Decimal('62')
    return avg,trend,forecast,safety,recommend,confidence,current

@csrf_exempt
@require_http_methods(['GET','POST'])
@roles_allowed('OWNER','MANAGER','WAREHOUSE')
def forecasting(request):
    horizon=max(7,min(90,int(request.GET.get('horizon',30) or 30)))
    if request.method=='POST':
        body=_json_body(request) or {};horizon=max(7,min(90,int(body.get('horizon',30) or 30)));products_qs=Product.objects.filter(company=request.company,is_active=True)[:250]
        warehouse=Warehouse.objects.filter(pk=body.get('warehouseId'),company=request.company).first() if body.get('warehouseId') else None
        for p in products_qs:
            avg,trend,forecast,safety,recommend,confidence,current=_forecast_row(request.company,p,warehouse,horizon)
            DemandForecast.objects.update_or_create(company=request.company,product=p,warehouse=warehouse,horizon_days=horizon,defaults={'avg_daily_demand':avg,'trend_percent':trend,'forecast_quantity':forecast,'safety_stock':safety,'recommended_purchase':recommend,'confidence':confidence})
        return JsonResponse({'ok':True,'generated':products_qs.count(),'horizon':horizon})
    rows=DemandForecast.objects.filter(company=request.company,horizon_days=horizon).select_related('product','warehouse').order_by('-recommended_purchase')[:100]
    if not rows.exists():
        preview=[]
        for p in Product.objects.filter(company=request.company,is_active=True)[:50]:
            avg,trend,forecast,safety,recommend,confidence,current=_forecast_row(request.company,p,None,horizon);preview.append({'product':p.name,'sku':p.sku,'warehouse':'All warehouses','currentStock':float(current),'avgDaily':float(avg),'trend':float(trend),'forecast':float(forecast),'safetyStock':float(safety),'recommendedPurchase':float(recommend),'confidence':float(confidence)})
        return JsonResponse({'horizon':horizon,'forecasts':sorted(preview,key=lambda x:x['recommendedPurchase'],reverse=True)})
    return JsonResponse({'horizon':horizon,'forecasts':[{'product':x.product.name,'sku':x.product.sku,'warehouse':x.warehouse.name if x.warehouse else 'All warehouses','currentStock':float(x.product.stock),'avgDaily':float(x.avg_daily_demand),'trend':float(x.trend_percent),'forecast':float(x.forecast_quantity),'safetyStock':float(x.safety_stock),'recommendedPurchase':float(x.recommended_purchase),'confidence':float(x.confidence)} for x in rows]})

def _assistant_answer(company, question):
    q=question.lower().strip(); today=timezone.localdate()
    if any(k in q for k in ['overdue','outstanding','receivable','credit']):
        rows=Customer.objects.filter(company=company,outstanding__gt=0).order_by('-outstanding')[:5];total=sum((x.outstanding for x in rows),Decimal('0'))
        return 'receivables', f"Top outstanding customers total ₹{float(total):,.0f} across the five largest balances.", {'customers':[{'name':x.name,'outstanding':float(x.outstanding),'limit':float(x.credit_limit)} for x in rows]}
    if any(k in q for k in ['run out','low stock','reorder','stockout']):
        rows=Product.objects.filter(company=company,is_active=True,stock__lte=F('reorder_level')).order_by('stock')[:8]
        return 'stock-risk', f'{len(rows)} priority products are at or below their reorder level.', {'products':[{'sku':x.sku,'name':x.name,'stock':float(x.stock),'reorderLevel':float(x.reorder_level)} for x in rows]}
    if any(k in q for k in ['sales','revenue','sold']):
        start=today.replace(day=1); total=Order.objects.filter(company=company,order_date__gte=start).exclude(status=Order.Status.CANCELLED).aggregate(v=Sum('total'))['v'] or 0
        count=Order.objects.filter(company=company,order_date__gte=start).exclude(status=Order.Status.CANCELLED).count()
        return 'sales', f'Month-to-date sales are ₹{float(total):,.0f} from {count} orders.', {'sales':float(total),'orders':count,'from':start.isoformat()}
    if any(k in q for k in ['purchase','buy','forecast','demand']):
        rows=DemandForecast.objects.filter(company=company).select_related('product').order_by('-recommended_purchase')[:5]
        return 'forecast', 'These products currently have the largest forecast-based purchase recommendations.', {'products':[{'sku':x.product.sku,'name':x.product.name,'recommendedPurchase':float(x.recommended_purchase),'confidence':float(x.confidence)} for x in rows]}
    if any(k in q for k in ['collection','payment']):
        start=today.replace(day=1); amount=Payment.objects.filter(company=company,payment_date__gte=start).aggregate(v=Sum('amount'))['v'] or 0
        return 'collections', f'Month-to-date customer collections are ₹{float(amount):,.0f}.', {'collections':float(amount),'from':start.isoformat()}
    return 'help', 'I can answer questions about sales, collections, overdue customers, low stock and forecast purchase recommendations using your SetuStock data.', {'examples':['Which products may run out?','Show overdue customers','What are month-to-date sales?','What should I reorder?']}

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def ai_assistant(request):
    if request.method=='GET':
        threads=AssistantThread.objects.filter(company=request.company,user=request.api_user).order_by('-updated_at')[:10]
        return JsonResponse({'threads':[{'id':t.id,'title':t.title,'updatedAt':t.updated_at.isoformat()} for t in threads],'capabilities':['sales','collections','receivables','stock risk','forecasting']})
    body=_json_body(request) or {}; question=str(body.get('question','')).strip()[:1200]
    if not question:return JsonResponse({'detail':'Ask a business question.'},status=400)
    thread=AssistantThread.objects.filter(pk=body.get('threadId'),company=request.company,user=request.api_user).first() if body.get('threadId') else None
    if not thread: thread=AssistantThread.objects.create(company=request.company,user=request.api_user,title=question[:80])
    AssistantMessage.objects.create(thread=thread,role='user',content=question)
    intent,answer,data=_assistant_answer(request.company,question);AssistantMessage.objects.create(thread=thread,role='assistant',content=answer,intent=intent,data=data);thread.save(update_fields=['updated_at'])
    return JsonResponse({'threadId':thread.id,'answer':answer,'intent':intent,'data':data})
