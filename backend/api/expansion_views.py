import json
from decimal import Decimal
from django.core import signing
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from .auth import api_auth_required
from .models import Customer, Invoice, PaymentTransaction, PaymentAllocation, PaymentPromise, CollectionTask, Warehouse, WarehouseBin, BinStock, PickList, PickListItem, CycleCount, Order, OrderItem, Product, Supplier, SupplierPortalAccess, SupplierPortalSubmission, PurchaseOrder


def _body(request):
    try: return json.loads(request.body or '{}')
    except json.JSONDecodeError: return None

def _money(v): return float(v or 0)

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def collections(request):
    company=request.company
    if request.method=='GET':
        receivable=Customer.objects.filter(company=company).aggregate(v=Sum('outstanding'))['v'] or Decimal('0')
        promises=PaymentPromise.objects.filter(company=company,status='Open').select_related('customer').order_by('promised_date')[:20]
        tasks=CollectionTask.objects.filter(company=company).select_related('customer','assigned_to').order_by('due_date')[:30]
        txns=PaymentTransaction.objects.filter(company=company).select_related('customer').order_by('-transaction_date','-id')[:30]
        return JsonResponse({'summary':{'receivable':_money(receivable),'openTasks':CollectionTask.objects.filter(company=company,status='Open').count(),'promiseAmount':_money(promises.aggregate(v=Sum('promised_amount'))['v'] or 0),'unmatched':PaymentTransaction.objects.filter(company=company,status='Unmatched').count()},'tasks':[{'id':x.id,'customer':x.customer.name,'amount':_money(x.amount_due),'due':x.due_date.isoformat(),'priority':x.priority,'status':x.status,'assignee':x.assigned_to.get_full_name() if x.assigned_to else ''} for x in tasks],'promises':[{'id':x.id,'customer':x.customer.name,'amount':_money(x.promised_amount),'date':x.promised_date.isoformat(),'status':x.status} for x in promises],'transactions':[{'id':x.id,'reference':x.reference,'customer':x.customer.name,'amount':_money(x.amount),'method':x.method,'date':x.transaction_date.isoformat(),'status':x.status} for x in txns]})
    data=_body(request) or {}; action=data.get('action')
    customer=Customer.objects.filter(company=company,pk=data.get('customerId')).first()
    if not customer: return JsonResponse({'detail':'Customer not found.'},status=404)
    if action=='promise':
        p=PaymentPromise.objects.create(company=company,customer=customer,promised_amount=data.get('amount',0),promised_date=data.get('date') or timezone.localdate(),notes=data.get('notes',''),created_by=request.api_user)
        return JsonResponse({'id':p.id,'status':p.status},status=201)
    if action=='task':
        t=CollectionTask.objects.create(company=company,customer=customer,assigned_to=request.api_user,due_date=data.get('date') or timezone.localdate(),amount_due=data.get('amount',customer.outstanding),priority=data.get('priority','Normal'),notes=data.get('notes',''))
        return JsonResponse({'id':t.id,'status':t.status},status=201)
    if action=='payment':
        with transaction.atomic():
            ref=data.get('reference') or f'PAY-{timezone.now().strftime("%y%m%d%H%M%S")}'
            pt=PaymentTransaction.objects.create(company=company,customer=customer,reference=ref,method=data.get('method','UPI'),amount=data.get('amount',0),transaction_date=data.get('date') or timezone.localdate(),created_by=request.api_user)
            remaining=Decimal(str(pt.amount))
            invoices=Invoice.objects.filter(company=company,order__customer=customer).exclude(status='Paid').order_by('invoice_date','id')
            for inv in invoices:
                allocated=inv.payment_allocations.aggregate(v=Sum('amount'))['v'] or Decimal('0')
                due=max(Decimal('0'),inv.total-allocated)
                use=min(remaining,due)
                if use>0: PaymentAllocation.objects.create(transaction=pt,invoice=inv,amount=use); remaining-=use
                if remaining<=0: break
            used=Decimal(str(pt.amount))-remaining
            pt.status='Matched' if remaining<=0 else ('Partial' if used>0 else 'Unmatched'); pt.save(update_fields=['status'])
            customer.outstanding=max(Decimal('0'),customer.outstanding-used); customer.save(update_fields=['outstanding'])
        return JsonResponse({'id':pt.id,'status':pt.status,'allocated':_money(used),'unapplied':_money(remaining)},status=201)
    return JsonResponse({'detail':'Unsupported action.'},status=400)


@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def wms(request):
    company=request.company
    if request.method=='GET':
        bins=WarehouseBin.objects.filter(warehouse__company=company).select_related('warehouse')[:50]
        picks=PickList.objects.filter(company=company).select_related('warehouse','assigned_to').prefetch_related('items').order_by('-id')[:20]
        counts=CycleCount.objects.filter(company=company).select_related('warehouse','bin','product').order_by('-id')[:20]
        return JsonResponse({'bins':[{'id':b.id,'code':b.code,'zone':b.zone,'warehouse':b.warehouse.name,'capacity':_money(b.capacity)} for b in bins],'picks':[{'id':p.id,'pickNo':p.pick_no,'warehouse':p.warehouse.name,'status':p.status,'lines':p.items.count()} for p in picks],'counts':[{'id':c.id,'warehouse':c.warehouse.name,'bin':c.bin.code,'product':c.product.name,'expected':_money(c.expected_qty),'counted':_money(c.counted_qty),'status':c.status} for c in counts]})
    data=_body(request) or {}; action=data.get('action')
    warehouse=Warehouse.objects.filter(company=company,pk=data.get('warehouseId')).first()
    if not warehouse: return JsonResponse({'detail':'Warehouse not found.'},status=404)
    if action=='create-bin':
        b=WarehouseBin.objects.create(warehouse=warehouse,code=data.get('code') or f'BIN-{WarehouseBin.objects.filter(warehouse=warehouse).count()+1}',zone=data.get('zone','General'),capacity=data.get('capacity',0))
        return JsonResponse({'id':b.id,'code':b.code},status=201)
    if action=='create-pick':
        p=PickList.objects.create(company=company,warehouse=warehouse,pick_no=f'PICK-{timezone.now().strftime("%y%m%d%H%M%S")}',status='Released',assigned_to=request.api_user)
        for oid in data.get('orderIds',[]):
            order=Order.objects.filter(company=company,pk=oid).first()
            if order:
                for item in order.items.select_related('product'):
                    PickListItem.objects.create(pick_list=p,order=order,product=item.product,requested_qty=item.quantity)
        return JsonResponse({'id':p.id,'pickNo':p.pick_no,'status':p.status},status=201)
    if action=='cycle-count':
        b=WarehouseBin.objects.filter(warehouse=warehouse,pk=data.get('binId')).first(); product=Product.objects.filter(company=company,pk=data.get('productId')).first()
        if not b or not product: return JsonResponse({'detail':'Bin or product not found.'},status=404)
        stock=BinStock.objects.filter(bin=b,product=product).first(); expected=stock.quantity if stock else 0
        c=CycleCount.objects.create(company=company,warehouse=warehouse,bin=b,product=product,expected_qty=expected,counted_qty=data.get('countedQty'),status='Counted',counted_by=request.api_user)
        return JsonResponse({'id':c.id,'variance':_money(Decimal(str(c.counted_qty or 0))-Decimal(str(expected)))},status=201)
    return JsonResponse({'detail':'Unsupported action.'},status=400)


SUPPLIER_PORTAL_SALT='setustock.supplier.portal'

@csrf_exempt
@require_POST
def supplier_portal_login(request):
    data=_body(request) or {}
    access=SupplierPortalAccess.objects.select_related('supplier','company').filter(email__iexact=data.get('email',''),is_active=True).first()
    if not access or not check_password(str(data.get('pin','')),access.pin_hash): return JsonResponse({'detail':'Invalid supplier portal credentials.'},status=401)
    access.last_login_at=timezone.now(); access.save(update_fields=['last_login_at'])
    token=signing.dumps({'aid':access.id,'sid':access.supplier_id,'co':access.company_id},salt=SUPPLIER_PORTAL_SALT,compress=True)
    return JsonResponse({'token':token,'supplier':{'id':access.supplier_id,'name':access.supplier.name,'company':access.company.name}})

def _supplier_access(request):
    h=request.headers.get('Authorization','')
    if not h.startswith('Supplier '): return None
    try:
        p=signing.loads(h[9:].strip(),salt=SUPPLIER_PORTAL_SALT,max_age=60*60*24*30)
        return SupplierPortalAccess.objects.select_related('supplier','company').get(pk=p['aid'],is_active=True)
    except Exception: return None

@csrf_exempt
@require_http_methods(['GET','POST'])
def supplier_portal(request):
    access=_supplier_access(request)
    if not access: return JsonResponse({'detail':'Supplier portal authentication required.'},status=401)
    supplier=access.supplier
    if request.method=='GET':
        pos=PurchaseOrder.objects.filter(company=access.company,supplier=supplier).order_by('-order_date','-id')[:30]
        return JsonResponse({'supplier':supplier.name,'purchaseOrders':[{'id':p.id,'poNo':p.po_no,'date':p.order_date.isoformat(),'status':p.status,'total':_money(p.total),'expected':p.expected_date.isoformat() if p.expected_date else None} for p in pos],'submissions':[{'id':x.id,'type':x.submission_type,'status':x.status,'payload':x.payload,'createdAt':x.created_at.isoformat()} for x in supplier.portal_submissions.order_by('-id')[:20]]})
    data=_body(request) or {}; po=PurchaseOrder.objects.filter(company=access.company,supplier=supplier,pk=data.get('purchaseOrderId')).first() if data.get('purchaseOrderId') else None
    sub=SupplierPortalSubmission.objects.create(company=access.company,supplier=supplier,purchase_order=po,submission_type=data.get('type','NOTE'),payload=data.get('payload') or {})
    return JsonResponse({'id':sub.id,'status':sub.status},status=201)

@api_auth_required
def supplier_portal_admin(request):
    rows=SupplierPortalSubmission.objects.filter(company=request.company).select_related('supplier','purchase_order').order_by('-id')[:50]
    return JsonResponse({'submissions':[{'id':x.id,'supplier':x.supplier.name,'po':x.purchase_order.po_no if x.purchase_order else '', 'type':x.submission_type,'status':x.status,'payload':x.payload} for x in rows]})
