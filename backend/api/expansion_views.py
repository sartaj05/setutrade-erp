import json
import secrets
from urllib.parse import urlencode
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.hashers import check_password
from django.core import signing
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .auth import api_auth_required
from .models import (
    AutomationRule, AutomationRun, BinStock, CollectionReminder, CollectionTask,
    Customer, CycleCount, DistributionNetwork, ExternalChannel, ExternalOrder,
    ExternalOrderItem, Invoice, LedgerEntry, NetworkMember, NetworkSnapshot,
    Notification, Order, OrderItem, Payment, PaymentAllocation, PaymentLink,
    PaymentPromise, PaymentTransaction, PickList, PickListItem, PickWave, PackingSlip, Product,
    PurchaseOrder, ReceivableFinanceExport, SupplierPortalAccess,
    SupplierPortalSubmission, Warehouse, WarehouseBin,
)


def _body(request):
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return None


def _money(value):
    return float(value or 0)



@require_http_methods(['GET'])
def public_payment_link(request, token):
    link = PaymentLink.objects.select_related('company', 'customer', 'invoice').filter(token=token, status='Active').first()
    if not link:
        return JsonResponse({'detail': 'Payment link is invalid or expired.'}, status=404)
    if link.expires_at and link.expires_at < timezone.now():
        link.status = 'Expired'; link.save(update_fields=['status'])
        return JsonResponse({'detail': 'Payment link has expired.'}, status=410)
    note = link.invoice.invoice_no if link.invoice else f'Customer {link.customer.code}'
    params = {'pa': link.company.upi_id, 'pn': link.company.name, 'am': str(link.amount), 'cu': 'INR', 'tn': note}
    upi_uri = f"upi://pay?{urlencode(params)}" if link.company.upi_id else ''
    return JsonResponse({'company': link.company.name, 'customer': link.customer.name, 'invoice': link.invoice.invoice_no if link.invoice else None, 'amount': _money(link.amount), 'expiresAt': link.expires_at.isoformat() if link.expires_at else None, 'upiUri': upi_uri, 'status': link.status})


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@api_auth_required
def collections(request):
    company = request.company
    if request.method == 'GET':
        receivable = Customer.objects.filter(company=company).aggregate(v=Sum('outstanding'))['v'] or Decimal('0')
        promises = PaymentPromise.objects.filter(company=company, status='Open').select_related('customer').order_by('promised_date')[:20]
        tasks = CollectionTask.objects.filter(company=company).select_related('customer', 'assigned_to').order_by('due_date')[:30]
        txns = PaymentTransaction.objects.filter(company=company).select_related('customer').order_by('-transaction_date', '-id')[:30]
        return JsonResponse({
            'summary': {
                'receivable': _money(receivable),
                'openTasks': CollectionTask.objects.filter(company=company, status='Open').count(),
                'promiseAmount': _money(promises.aggregate(v=Sum('promised_amount'))['v'] or 0),
                'unmatched': PaymentTransaction.objects.filter(company=company, status='Unmatched').count(),
                'activePaymentLinks': PaymentLink.objects.filter(company=company, status='Active').count(),
                'scheduledReminders': CollectionReminder.objects.filter(company=company, status='Scheduled').count(),
            },
            'tasks': [
                {'id': x.id, 'customerId': x.customer_id, 'customer': x.customer.name, 'amount': _money(x.amount_due), 'due': x.due_date.isoformat(), 'priority': x.priority, 'status': x.status, 'assignee': x.assigned_to.get_full_name() if x.assigned_to else ''}
                for x in tasks
            ],
            'promises': [
                {'id': x.id, 'customerId': x.customer_id, 'customer': x.customer.name, 'amount': _money(x.promised_amount), 'date': x.promised_date.isoformat(), 'status': x.status}
                for x in promises
            ],
            'transactions': [
                {'id': x.id, 'reference': x.reference, 'customerId': x.customer_id, 'customer': x.customer.name, 'amount': _money(x.amount), 'method': x.method, 'date': x.transaction_date.isoformat(), 'status': x.status}
                for x in txns
            ],
        })

    data = _body(request) or {}
    action = data.get('action')
    customer = Customer.objects.filter(company=company, pk=data.get('customerId')).first()
    if not customer:
        return JsonResponse({'detail': 'Customer not found.'}, status=404)

    if action == 'payment-link':
        invoice = Invoice.objects.filter(company=company, pk=data.get('invoiceId')).first() if data.get('invoiceId') else None
        link = PaymentLink.objects.create(
            company=company,
            customer=customer,
            invoice=invoice,
            token=secrets.token_urlsafe(32),
            amount=data.get('amount') or (invoice.total if invoice else customer.outstanding),
            expires_at=timezone.now() + timedelta(days=7),
        )
        return JsonResponse({'id': link.id, 'token': link.token, 'amount': _money(link.amount), 'status': link.status}, status=201)

    if action == 'reminder':
        invoice = Invoice.objects.filter(company=company, pk=data.get('invoiceId')).first() if data.get('invoiceId') else None
        reminder = CollectionReminder.objects.create(
            company=company,
            customer=customer,
            invoice=invoice,
            channel=data.get('channel', 'WhatsApp'),
            scheduled_for=data.get('scheduledFor') or timezone.now(),
            message=data.get('message') or f'Payment reminder: {customer.name} has {customer.outstanding} outstanding.',
        )
        return JsonResponse({'id': reminder.id, 'status': reminder.status}, status=201)

    if action == 'statement':
        entries = [
            {'reference': x.reference, 'type': x.entry_type, 'date': x.entry_date.isoformat(), 'amount': _money(x.amount), 'dueDate': x.due_date.isoformat() if x.due_date else None}
            for x in customer.ledger_entries.order_by('entry_date', 'id')
        ]
        return JsonResponse({'customer': customer.name, 'outstanding': _money(customer.outstanding), 'entries': entries})

    if action == 'finance-export':
        invoices = Invoice.objects.filter(company=company, order__customer=customer).exclude(status='Paid').select_related('order')
        payload = [
            {'invoiceNo': i.invoice_no, 'date': i.invoice_date.isoformat(), 'dueDate': i.due_date.isoformat() if i.due_date else None, 'buyer': customer.name, 'gstin': customer.gstin, 'amount': _money(i.total)}
            for i in invoices
        ]
        total = sum((Decimal(str(x['amount'])) for x in payload), Decimal('0'))
        export = ReceivableFinanceExport.objects.create(
            company=company,
            export_no=f'RF-{timezone.now().strftime("%y%m%d%H%M%S%f")}',
            invoice_count=len(payload),
            total_amount=total,
            payload=payload,
            created_by=request.api_user,
        )
        return JsonResponse({'id': export.id, 'exportNo': export.export_no, 'invoiceCount': export.invoice_count, 'total': _money(total), 'payload': payload}, status=201)

    if action == 'promise':
        promise = PaymentPromise.objects.create(
            company=company,
            customer=customer,
            promised_amount=data.get('amount', 0),
            promised_date=data.get('date') or timezone.localdate(),
            notes=data.get('notes', ''),
            created_by=request.api_user,
        )
        return JsonResponse({'id': promise.id, 'status': promise.status}, status=201)

    if action == 'task':
        task = CollectionTask.objects.create(
            company=company,
            customer=customer,
            assigned_to=request.api_user,
            due_date=data.get('date') or timezone.localdate(),
            amount_due=data.get('amount', customer.outstanding),
            priority=data.get('priority', 'Normal'),
            notes=data.get('notes', ''),
        )
        return JsonResponse({'id': task.id, 'status': task.status}, status=201)

    if action == 'payment':
        amount = Decimal(str(data.get('amount', 0)))
        if amount <= 0:
            return JsonResponse({'detail': 'Payment amount must be greater than zero.'}, status=400)
        with transaction.atomic():
            reference = data.get('reference') or f'PAY-{timezone.now().strftime("%y%m%d%H%M%S%f")}'
            txn = PaymentTransaction.objects.create(
                company=company,
                customer=customer,
                reference=reference,
                method=data.get('method', 'UPI'),
                amount=amount,
                transaction_date=data.get('date') or timezone.localdate(),
                created_by=request.api_user,
            )
            remaining = amount
            touched = []
            invoices = Invoice.objects.filter(company=company, order__customer=customer).exclude(status='Paid').order_by('invoice_date', 'id')
            for invoice in invoices:
                allocated = invoice.payment_allocations.aggregate(v=Sum('amount'))['v'] or Decimal('0')
                due = max(Decimal('0'), invoice.total - allocated)
                use = min(remaining, due)
                if use > 0:
                    PaymentAllocation.objects.create(transaction=txn, invoice=invoice, amount=use)
                    touched.append(invoice)
                    remaining -= use
                if remaining <= 0:
                    break
            used = amount - remaining
            txn.status = 'Matched' if remaining <= 0 else ('Partial' if used > 0 else 'Unmatched')
            txn.save(update_fields=['status'])
            customer.outstanding = max(Decimal('0'), customer.outstanding - used)
            customer.save(update_fields=['outstanding'])
            receipt = None
            if used > 0:
                receipt = Payment.objects.create(
                    company=company,
                    receipt_no=f'RCPT-{timezone.now().strftime("%y%m%d%H%M%S%f")}',
                    customer=customer,
                    amount=used,
                    method=data.get('method', 'UPI') if data.get('method', 'UPI') in dict(Payment.Method.choices) else 'Other',
                    reference=reference,
                    payment_date=data.get('date') or timezone.localdate(),
                    notes='Auto-posted from reconciliation',
                    recorded_by=request.api_user,
                )
                LedgerEntry.objects.create(company=company, customer=customer, entry_type='Payment', reference=receipt.receipt_no, amount=-used, entry_date=receipt.payment_date, note='Reconciled payment')
            for invoice in touched:
                allocated = invoice.payment_allocations.aggregate(v=Sum('amount'))['v'] or Decimal('0')
                invoice.status = 'Paid' if allocated >= invoice.total else 'Partial'
                invoice.save(update_fields=['status'])
        return JsonResponse({'id': txn.id, 'status': txn.status, 'allocated': _money(used), 'unapplied': _money(remaining), 'receiptNo': receipt.receipt_no if receipt else None}, status=201)

    return JsonResponse({'detail': 'Unsupported action.'}, status=400)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@api_auth_required
def wms(request):
    company = request.company
    if request.method == 'GET':
        bins = WarehouseBin.objects.filter(warehouse__company=company).select_related('warehouse')[:50]
        picks = PickList.objects.filter(company=company).select_related('warehouse', 'assigned_to').prefetch_related('items').order_by('-id')[:20]
        counts = CycleCount.objects.filter(company=company).select_related('warehouse', 'bin', 'product').order_by('-id')[:20]
        waves = PickWave.objects.filter(company=company).select_related('warehouse').prefetch_related('pick_lists').order_by('-id')[:20]
        packs = PackingSlip.objects.filter(company=company).select_related('warehouse', 'order').order_by('-id')[:20]
        return JsonResponse({
            'bins': [{'id': b.id, 'code': b.code, 'zone': b.zone, 'warehouse': b.warehouse.name, 'capacity': _money(b.capacity)} for b in bins],
            'picks': [{'id': p.id, 'pickNo': p.pick_no, 'warehouse': p.warehouse.name, 'status': p.status, 'lines': p.items.count()} for p in picks],
            'counts': [{'id': c.id, 'warehouse': c.warehouse.name, 'bin': c.bin.code, 'product': c.product.name, 'expected': _money(c.expected_qty), 'counted': _money(c.counted_qty), 'status': c.status} for c in counts],
            'waves': [{'id': w.id, 'waveNo': w.wave_no, 'warehouse': w.warehouse.name, 'status': w.status, 'pickCount': w.pick_lists.count()} for w in waves],
            'packing': [{'id': x.id, 'packageNo': x.package_no, 'order': x.order.order_no, 'warehouse': x.warehouse.name, 'cartons': x.carton_count, 'weightKg': _money(x.weight_kg), 'status': x.status} for x in packs],
        })

    data = _body(request) or {}
    action = data.get('action')
    warehouse = Warehouse.objects.filter(company=company, pk=data.get('warehouseId')).first()
    if not warehouse:
        return JsonResponse({'detail': 'Warehouse not found.'}, status=404)

    if action == 'create-bin':
        code = data.get('code') or f'BIN-{WarehouseBin.objects.filter(warehouse=warehouse).count() + 1}'
        bin_obj = WarehouseBin.objects.create(warehouse=warehouse, code=code, zone=data.get('zone', 'General'), capacity=data.get('capacity', 0))
        return JsonResponse({'id': bin_obj.id, 'code': bin_obj.code}, status=201)

    if action == 'create-pick':
        pick = PickList.objects.create(
            company=company,
            warehouse=warehouse,
            pick_no=f'PICK-{timezone.now().strftime("%y%m%d%H%M%S%f")}',
            status='Released',
            assigned_to=request.api_user,
        )
        for order_id in data.get('orderIds', []):
            order = Order.objects.filter(company=company, pk=order_id).first()
            if not order:
                continue
            for item in order.items.select_related('product'):
                source_bin = WarehouseBin.objects.filter(warehouse=warehouse, stocks__product=item.product, stocks__quantity__gt=0).first()
                PickListItem.objects.create(pick_list=pick, order=order, product=item.product, source_bin=source_bin, requested_qty=item.quantity)
        return JsonResponse({'id': pick.id, 'pickNo': pick.pick_no, 'status': pick.status}, status=201)

    if action == 'create-wave':
        wave = PickWave.objects.create(company=company, warehouse=warehouse, wave_no=f'WAVE-{timezone.now().strftime("%y%m%d%H%M%S%f")}', status='Released', created_by=request.api_user)
        picks = PickList.objects.filter(company=company, warehouse=warehouse, pk__in=data.get('pickIds', []))
        wave.pick_lists.set(picks)
        return JsonResponse({'id': wave.id, 'waveNo': wave.wave_no, 'pickCount': wave.pick_lists.count(), 'status': wave.status}, status=201)

    if action == 'pack-order':
        order = Order.objects.filter(company=company, warehouse=warehouse, pk=data.get('orderId')).first()
        if not order:
            return JsonResponse({'detail': 'Order not found.'}, status=404)
        pick = PickList.objects.filter(company=company, warehouse=warehouse, pk=data.get('pickId')).first() if data.get('pickId') else None
        slip = PackingSlip.objects.create(company=company, warehouse=warehouse, order=order, pick_list=pick, package_no=f'PKG-{timezone.now().strftime("%y%m%d%H%M%S%f")}', carton_count=data.get('cartons', 1), weight_kg=data.get('weightKg', 0), status='Packed', packed_by=request.api_user, packed_at=timezone.now())
        if pick and pick.status != 'Complete':
            pick.status = 'Complete'; pick.save(update_fields=['status'])
        return JsonResponse({'id': slip.id, 'packageNo': slip.package_no, 'status': slip.status}, status=201)

    if action == 'complete-pick':
        pick = PickList.objects.filter(company=company, warehouse=warehouse, pk=data.get('pickId')).prefetch_related('items').first()
        if not pick:
            return JsonResponse({'detail': 'Pick list not found.'}, status=404)
        for item in pick.items.all():
            item.picked_qty = item.requested_qty
            item.save(update_fields=['picked_qty'])
        pick.status = 'Complete'; pick.save(update_fields=['status'])
        return JsonResponse({'id': pick.id, 'status': pick.status})

    if action == 'post-count':
        count = CycleCount.objects.filter(company=company, warehouse=warehouse, pk=data.get('countId'), status='Counted').select_related('bin', 'product').first()
        if not count or count.counted_qty is None:
            return JsonResponse({'detail': 'Counted cycle count not found.'}, status=404)
        stock, _ = BinStock.objects.get_or_create(bin=count.bin, product=count.product, defaults={'quantity': 0})
        delta = count.counted_qty - stock.quantity
        stock.quantity = count.counted_qty; stock.save(update_fields=['quantity'])
        from .models import StockBalance
        wh_stock, _ = StockBalance.objects.get_or_create(warehouse=warehouse, product=count.product, defaults={'quantity': 0, 'reserved': 0})
        wh_stock.quantity = max(Decimal('0'), wh_stock.quantity + delta); wh_stock.save(update_fields=['quantity'])
        total = StockBalance.objects.filter(product=count.product).aggregate(v=Sum('quantity'))['v'] or Decimal('0')
        count.product.stock = total; count.product.save(update_fields=['stock'])
        count.status = 'Posted'; count.save(update_fields=['status'])
        return JsonResponse({'id': count.id, 'status': count.status, 'variance': _money(delta), 'warehouseStock': _money(wh_stock.quantity)})

    if action == 'cycle-count':
        bin_obj = WarehouseBin.objects.filter(warehouse=warehouse, pk=data.get('binId')).first()
        product = Product.objects.filter(company=company, pk=data.get('productId')).first()
        if not bin_obj or not product:
            return JsonResponse({'detail': 'Bin or product not found.'}, status=404)
        stock = BinStock.objects.filter(bin=bin_obj, product=product).first()
        expected = stock.quantity if stock else Decimal('0')
        count = CycleCount.objects.create(
            company=company,
            warehouse=warehouse,
            bin=bin_obj,
            product=product,
            expected_qty=expected,
            counted_qty=data.get('countedQty'),
            status='Counted',
            counted_by=request.api_user,
        )
        return JsonResponse({'id': count.id, 'variance': _money(Decimal(str(count.counted_qty or 0)) - expected)}, status=201)

    return JsonResponse({'detail': 'Unsupported action.'}, status=400)


SUPPLIER_PORTAL_SALT = 'setustock.supplier.portal'


@csrf_exempt
@require_POST
def supplier_portal_login(request):
    data = _body(request) or {}
    access = SupplierPortalAccess.objects.select_related('supplier', 'company').filter(email__iexact=data.get('email', ''), is_active=True).first()
    if not access or not check_password(str(data.get('pin', '')), access.pin_hash):
        return JsonResponse({'detail': 'Invalid supplier portal credentials.'}, status=401)
    access.last_login_at = timezone.now()
    access.save(update_fields=['last_login_at'])
    token = signing.dumps({'aid': access.id, 'sid': access.supplier_id, 'co': access.company_id}, salt=SUPPLIER_PORTAL_SALT, compress=True)
    return JsonResponse({'token': token, 'supplier': {'id': access.supplier_id, 'name': access.supplier.name, 'company': access.company.name}})


def _supplier_access(request):
    header = request.headers.get('Authorization', '')
    if not header.startswith('Supplier '):
        return None
    try:
        payload = signing.loads(header[9:].strip(), salt=SUPPLIER_PORTAL_SALT, max_age=60 * 60 * 24 * 30)
        return SupplierPortalAccess.objects.select_related('supplier', 'company').get(pk=payload['aid'], is_active=True)
    except (signing.BadSignature, signing.SignatureExpired, SupplierPortalAccess.DoesNotExist, KeyError):
        return None


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def supplier_portal(request):
    access = _supplier_access(request)
    if not access:
        return JsonResponse({'detail': 'Supplier portal authentication required.'}, status=401)
    supplier = access.supplier
    if request.method == 'GET':
        purchase_orders = PurchaseOrder.objects.filter(company=access.company, supplier=supplier).order_by('-order_date', '-id')[:30]
        return JsonResponse({
            'supplier': supplier.name,
            'purchaseOrders': [{'id': p.id, 'poNo': p.po_no, 'date': p.order_date.isoformat(), 'status': p.status, 'total': _money(p.total), 'expected': p.expected_date.isoformat() if p.expected_date else None} for p in purchase_orders],
            'submissions': [{'id': x.id, 'type': x.submission_type, 'status': x.status, 'payload': x.payload, 'createdAt': x.created_at.isoformat()} for x in supplier.portal_submissions.order_by('-id')[:20]],
        })
    data = _body(request) or {}
    purchase_order = PurchaseOrder.objects.filter(company=access.company, supplier=supplier, pk=data.get('purchaseOrderId')).first() if data.get('purchaseOrderId') else None
    submission = SupplierPortalSubmission.objects.create(
        company=access.company,
        supplier=supplier,
        purchase_order=purchase_order,
        submission_type=data.get('type', 'NOTE'),
        payload=data.get('payload') or {},
    )
    return JsonResponse({'id': submission.id, 'status': submission.status}, status=201)


@api_auth_required
def supplier_portal_admin(request):
    rows = SupplierPortalSubmission.objects.filter(company=request.company).select_related('supplier', 'purchase_order').order_by('-id')[:50]
    return JsonResponse({'submissions': [{'id': x.id, 'supplier': x.supplier.name, 'po': x.purchase_order.po_no if x.purchase_order else '', 'type': x.submission_type, 'status': x.status, 'payload': x.payload} for x in rows]})


def _condition_matches(conditions, payload):
    for key, expected in (conditions or {}).items():
        actual = payload.get(key)
        if isinstance(expected, dict):
            if 'gte' in expected and Decimal(str(actual or 0)) < Decimal(str(expected['gte'])):
                return False
            if 'gt' in expected and Decimal(str(actual or 0)) <= Decimal(str(expected['gt'])):
                return False
            if 'eq' in expected and actual != expected['eq']:
                return False
        elif actual != expected:
            return False
    return True


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@api_auth_required
def automations(request):
    if request.method == 'GET':
        rules = AutomationRule.objects.filter(company=request.company).order_by('-id')
        runs = AutomationRun.objects.filter(company=request.company).select_related('rule').order_by('-id')[:30]
        return JsonResponse({
            'rules': [{'id': r.id, 'name': r.name, 'event': r.event, 'conditions': r.conditions, 'actions': r.actions, 'active': r.is_active, 'lastRun': r.last_run_at.isoformat() if r.last_run_at else None} for r in rules],
            'runs': [{'id': x.id, 'rule': x.rule.name, 'event': x.event, 'status': x.status, 'actions': x.actions_executed, 'createdAt': x.created_at.isoformat()} for x in runs],
        })

    data = _body(request) or {}
    action = data.get('action', 'create')
    if action == 'create':
        rule = AutomationRule.objects.create(
            company=request.company,
            name=data.get('name', 'New automation'),
            event=data.get('event', 'invoice.overdue'),
            conditions=data.get('conditions') or {},
            actions=data.get('actions') or [],
            created_by=request.api_user,
        )
        return JsonResponse({'id': rule.id, 'name': rule.name}, status=201)

    if action == 'test':
        payload = data.get('payload') or {}
        event = data.get('event', 'invoice.overdue')
        executed = []
        for rule in AutomationRule.objects.filter(company=request.company, event=event, is_active=True):
            if not _condition_matches(rule.conditions, payload):
                continue
            action_names = []
            for item in rule.actions:
                kind = item.get('type') if isinstance(item, dict) else str(item)
                action_names.append(kind)
                if kind == 'notify':
                    Notification.objects.create(
                        company=request.company,
                        user=request.api_user,
                        title=item.get('title', 'Automation alert'),
                        message=item.get('message', rule.name),
                        level='info',
                        module=item.get('module', 'dashboard'),
                    )
                elif kind == 'create_collection_task' and payload.get('customerId'):
                    customer = Customer.objects.filter(company=request.company, pk=payload['customerId']).first()
                    if customer:
                        CollectionTask.objects.create(
                            company=request.company,
                            customer=customer,
                            assigned_to=request.api_user,
                            due_date=timezone.localdate(),
                            amount_due=customer.outstanding,
                            priority='High',
                            notes=f'Automation: {rule.name}',
                        )
                elif kind == 'schedule_reminder' and payload.get('customerId'):
                    customer = Customer.objects.filter(company=request.company, pk=payload['customerId']).first()
                    if customer:
                        CollectionReminder.objects.create(company=request.company, customer=customer, channel=item.get('channel', 'WhatsApp'), scheduled_for=timezone.now(), message=item.get('message') or f'Payment reminder for {customer.name}: {customer.outstanding} outstanding.')
            AutomationRun.objects.create(
                company=request.company,
                rule=rule,
                event=event,
                entity_type=data.get('entityType', ''),
                entity_id=str(data.get('entityId', '')),
                actions_executed=action_names,
            )
            rule.last_run_at = timezone.now()
            rule.save(update_fields=['last_run_at'])
            executed.append({'rule': rule.name, 'actions': action_names})
        return JsonResponse({'matched': len(executed), 'executed': executed})

    return JsonResponse({'detail': 'Unsupported action.'}, status=400)


def _ingest_external_order(company, channel, data):
    external_id = str(data.get('externalId') or f'EXT-{timezone.now().strftime("%y%m%d%H%M%S%f")}')
    order, created = ExternalOrder.objects.get_or_create(
        channel=channel,
        external_id=external_id,
        defaults={
            'company': company,
            'customer_name': data.get('customerName', 'External buyer'),
            'customer_phone': data.get('phone', ''),
            'ship_to': data.get('shipTo') or {},
            'total': data.get('total', 0),
            'raw_payload': data,
        },
    )
    if created:
        for row in data.get('items', []):
            sku = str(row.get('sku', ''))
            product = Product.objects.filter(company=company, sku=sku).first()
            ExternalOrderItem.objects.create(
                external_order=order,
                external_sku=sku,
                product=product,
                name=row.get('name') or (product.name if product else sku),
                quantity=row.get('quantity', 1),
                unit_price=row.get('unitPrice', 0),
            )
    channel.last_sync_at = timezone.now()
    channel.save(update_fields=['last_sync_at'])
    return order, created


@csrf_exempt
@require_POST
def channel_webhook(request, channel_id):
    channel = ExternalChannel.objects.select_related('company').filter(pk=channel_id, is_active=True).first()
    if not channel:
        return JsonResponse({'detail': 'Channel not found.'}, status=404)
    expected_key = str((channel.settings or {}).get('webhookKey', ''))
    supplied_key = request.headers.get('X-Channel-Key', '')
    if not expected_key or not secrets.compare_digest(expected_key, supplied_key):
        return JsonResponse({'detail': 'Invalid channel webhook key.'}, status=401)
    data = _body(request) or {}
    order, created = _ingest_external_order(channel.company, channel, data)
    return JsonResponse({'id': order.id, 'created': created, 'status': order.status}, status=201 if created else 200)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@api_auth_required
def channels(request):
    company = request.company
    if request.method == 'GET':
        channel_rows = ExternalChannel.objects.filter(company=company).order_by('name')
        orders = ExternalOrder.objects.filter(company=company).select_related('channel').prefetch_related('items').order_by('-id')[:50]
        return JsonResponse({
            'channels': [{'id': c.id, 'name': c.name, 'provider': c.provider, 'active': c.is_active, 'storeId': c.external_store_id, 'lastSync': c.last_sync_at.isoformat() if c.last_sync_at else None, 'webhookConfigured': bool((c.settings or {}).get('webhookKey'))} for c in channel_rows],
            'orders': [{'id': o.id, 'externalId': o.external_id, 'channel': o.channel.name, 'provider': o.channel.provider, 'customer': o.customer_name, 'phone': o.customer_phone, 'total': _money(o.total), 'status': o.status, 'receivedAt': o.received_at.isoformat(), 'items': [{'sku': i.external_sku, 'name': i.name, 'qty': _money(i.quantity), 'price': _money(i.unit_price), 'matched': bool(i.product_id)} for i in o.items.all()]} for o in orders],
        })

    data = _body(request) or {}
    action = data.get('action', 'create-channel')
    if action == 'create-channel':
        settings_data = data.get('settings') or {}
        settings_data.setdefault('webhookKey', secrets.token_urlsafe(24))
        channel = ExternalChannel.objects.create(
            company=company,
            name=data.get('name', 'Web Store'),
            provider=data.get('provider', 'WEBSITE'),
            external_store_id=data.get('storeId', ''),
            settings=settings_data,
        )
        return JsonResponse({'id': channel.id, 'name': channel.name, 'provider': channel.provider, 'webhookKey': settings_data['webhookKey']}, status=201)

    if action == 'ingest-order':
        channel = ExternalChannel.objects.filter(company=company, pk=data.get('channelId'), is_active=True).first()
        if not channel:
            return JsonResponse({'detail': 'Channel not found.'}, status=404)
        order, created = _ingest_external_order(company, channel, data)
        return JsonResponse({'id': order.id, 'created': created, 'status': order.status}, status=201 if created else 200)

    if action == 'convert':
        external = ExternalOrder.objects.filter(company=company, pk=data.get('id')).select_related('channel').prefetch_related('items').first()
        customer = Customer.objects.filter(company=company, pk=data.get('customerId')).first()
        warehouse = Warehouse.objects.filter(company=company, pk=data.get('warehouseId')).first()
        if not external or not customer or not warehouse:
            return JsonResponse({'detail': 'Order, customer or warehouse missing.'}, status=400)
        if external.converted_order_id:
            return JsonResponse({'detail': 'Already converted.', 'orderId': external.converted_order_id})
        with transaction.atomic():
            order = Order.objects.create(
                company=company,
                branch=request.branch,
                warehouse=warehouse,
                order_no=f'CH-{timezone.now().strftime("%y%m%d%H%M%S%f")}',
                customer=customer,
                order_date=timezone.localdate(),
                status='Draft',
                created_by=request.api_user,
                notes=f'{external.channel.provider} {external.external_id}',
            )
            subtotal = Decimal('0')
            tax_total = Decimal('0')
            for row in external.items.all():
                if not row.product_id:
                    continue
                line = Decimal(str(row.quantity)) * Decimal(str(row.unit_price))
                tax_amount = line * row.product.gst_rate / Decimal('100')
                subtotal += line
                tax_total += tax_amount
                OrderItem.objects.create(
                    order=order,
                    product=row.product,
                    quantity=row.quantity,
                    unit_price=row.unit_price,
                    gst_rate=row.product.gst_rate,
                    taxable_amount=line,
                    tax_amount=tax_amount,
                    line_total=line + tax_amount,
                )
            order.subtotal = subtotal
            order.tax = tax_total
            order.total = subtotal + tax_total
            order.save(update_fields=['subtotal', 'tax', 'total'])
            external.converted_order = order
            external.status = 'Converted'
            external.save(update_fields=['converted_order', 'status'])
        return JsonResponse({'orderId': order.id, 'orderNo': order.order_no, 'total': _money(order.total)})

    return JsonResponse({'detail': 'Unsupported action.'}, status=400)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@api_auth_required
def distribution_networks(request):
    company = request.company
    if request.method == 'GET':
        owned = DistributionNetwork.objects.filter(owner_company=company, is_active=True).prefetch_related('members__company')
        payload = []
        for network in owned:
            members = []
            for member in network.members.filter(is_active=True).select_related('company'):
                snapshot = member.snapshots.order_by('-snapshot_date', '-id').first()
                members.append({
                    'id': member.id,
                    'company': member.company.name,
                    'region': member.region,
                    'territory': member.territory,
                    'shareInventory': member.share_inventory,
                    'shareSales': member.share_secondary_sales,
                    'snapshot': ({
                        'date': snapshot.snapshot_date.isoformat(),
                        'inventoryValue': _money(snapshot.inventory_value),
                        'stockUnits': _money(snapshot.stock_units),
                        'secondarySales': _money(snapshot.secondary_sales),
                        'openOrders': snapshot.open_orders,
                        'products': snapshot.product_summary,
                    } if snapshot else None),
                })
            payload.append({'id': network.id, 'name': network.name, 'code': network.code, 'members': members})
        memberships = NetworkMember.objects.filter(company=company).select_related('network', 'network__owner_company')
        return JsonResponse({
            'ownedNetworks': payload,
            'memberships': [{'id': m.id, 'network': m.network.name, 'owner': m.network.owner_company.name, 'region': m.region, 'territory': m.territory, 'status': 'Active' if m.is_active else 'Pending'} for m in memberships],
        })

    data = _body(request) or {}
    action = data.get('action', 'create-network')
    if action == 'create-network':
        code = data.get('code') or f'NET-{timezone.now().strftime("%y%m%d%H%M%S%f")}'
        network = DistributionNetwork.objects.create(owner_company=company, name=data.get('name', 'Distribution Network'), code=code)
        NetworkMember.objects.get_or_create(network=network, company=company, defaults={'region': company.state, 'territory': 'Head Office'})
        return JsonResponse({'id': network.id, 'name': network.name, 'code': network.code}, status=201)

    if action == 'accept-membership':
        membership = NetworkMember.objects.filter(network_id=data.get('networkId'), company=company, is_active=False).select_related('network').first()
        if not membership:
            return JsonResponse({'detail': 'Pending membership invitation not found.'}, status=404)
        membership.is_active = True
        membership.save(update_fields=['is_active'])
        return JsonResponse({'id': membership.id, 'network': membership.network.name, 'status': 'Active'})

    network = DistributionNetwork.objects.filter(owner_company=company, pk=data.get('networkId')).first()
    if not network:
        return JsonResponse({'detail': 'Network not found.'}, status=404)

    if action == 'add-member':
        from .models import Company
        member_company = Company.objects.filter(pk=data.get('companyId'), is_active=True).first()
        if not member_company:
            return JsonResponse({'detail': 'Member company not found.'}, status=404)
        member, _ = NetworkMember.objects.get_or_create(
            network=network,
            company=member_company,
            defaults={'region': data.get('region', ''), 'territory': data.get('territory', ''), 'is_active': False},
        )
        return JsonResponse({'id': member.id, 'company': member.company.name, 'status': 'Pending acceptance'}, status=201)

    if action == 'snapshot':
        member = NetworkMember.objects.filter(network=network, pk=data.get('memberId'), is_active=True).select_related('company').first()
        if not member:
            return JsonResponse({'detail': 'Active member not found.'}, status=404)
        member_company = member.company
        stock_units = Product.objects.filter(company=member_company, is_active=True).aggregate(v=Sum('stock'))['v'] or Decimal('0')
        inventory_value = sum((p.stock * p.purchase_price for p in Product.objects.filter(company=member_company, is_active=True)), Decimal('0'))
        sales = Order.objects.filter(company=member_company, order_date__gte=timezone.localdate().replace(day=1)).aggregate(v=Sum('total'))['v'] or Decimal('0')
        open_orders = Order.objects.filter(company=member_company).exclude(status__in=['Dispatched', 'Cancelled']).count()
        products = []
        if member.share_inventory:
            products = [{'sku': p.sku, 'name': p.name, 'stock': _money(p.stock)} for p in Product.objects.filter(company=member_company, is_active=True).order_by('stock')[:20]]
        snapshot, _ = NetworkSnapshot.objects.update_or_create(
            network=network,
            member=member,
            snapshot_date=timezone.localdate(),
            defaults={
                'inventory_value': inventory_value if member.share_inventory else 0,
                'stock_units': stock_units if member.share_inventory else 0,
                'secondary_sales': sales if member.share_secondary_sales else 0,
                'open_orders': open_orders,
                'product_summary': products,
            },
        )
        return JsonResponse({'id': snapshot.id, 'date': snapshot.snapshot_date.isoformat(), 'inventoryValue': _money(snapshot.inventory_value), 'secondarySales': _money(snapshot.secondary_sales)})

    return JsonResponse({'detail': 'Unsupported action.'}, status=400)
