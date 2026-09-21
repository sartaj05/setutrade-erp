import json
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .auth import api_auth_required
from . import models as m
from .services import audit


def _body(request):
    try: return json.loads(request.body or '{}')
    except json.JSONDecodeError: return {}

def _money(v): return float(v or 0)
def _dt(v): return v.isoformat() if v else None
def _guard(request, roles):
    return None if request.api_user.profile.role in roles else JsonResponse({'detail':'You do not have access to this module.'},status=403)
def _pick(qs, pk):
    return qs.filter(pk=pk).first() if pk else qs.first()

# Phase 27
@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def product_master(request):
    denied=_guard(request,['OWNER','MANAGER','WAREHOUSE','ACCOUNTANT'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        profiles=m.ProductMasterProfile.objects.filter(company=company).select_related('product','preferred_supplier').order_by('product__name')
        changes=m.ProductChangeRequest.objects.filter(company=company).select_related('product','requested_by').order_by('-created_at')[:50]
        low=profiles.filter(data_quality_score__lt=80).count()
        return JsonResponse({'summary':{'products':profiles.count(),'qualityIssues':low,'pendingChanges':changes.filter(status='Pending').count(),'governed':profiles.filter(governance_status='Approved').count()},'products':[{'id':x.id,'productId':x.product_id,'sku':x.product.sku,'name':x.product.name,'brand':x.brand,'manufacturer':x.manufacturer,'hsn':x.product.hsn_code,'gst':_money(x.product.gst_rate),'barcode':x.product.barcode or '','uom':x.primary_uom,'purchaseUom':x.purchase_uom,'salesUom':x.sales_uom,'mrp':_money(x.mrp),'dealerPrice':_money(x.dealer_price),'distributorPrice':_money(x.distributor_price),'batchRequired':x.batch_required,'serialRequired':x.serial_required,'expiryRequired':x.expiry_required,'preferredSupplier':x.preferred_supplier.name if x.preferred_supplier else '', 'quality':x.data_quality_score,'status':x.governance_status} for x in profiles], 'changes':[{'id':c.id,'product':c.product.name,'type':c.change_type,'changes':c.requested_changes,'reason':c.reason,'status':c.status,'requestedBy':c.requested_by.get_full_name() if c.requested_by else ''} for c in changes]})
    data=_body(request); action=data.get('action','refresh-quality')
    if action=='refresh-quality':
        updated=0
        for p in m.Product.objects.filter(company=company):
            profile,_=m.ProductMasterProfile.objects.get_or_create(company=company,product=p,defaults={'primary_uom':p.unit,'purchase_uom':p.unit,'sales_uom':p.unit,'mrp':p.sell_price,'dealer_price':p.sell_price,'distributor_price':p.sell_price,'minimum_stock':p.reorder_level,'reorder_quantity':p.reorder_level,'updated_by':request.api_user})
            checks=[bool(p.sku),bool(p.name),bool(p.hsn_code),p.gst_rate is not None,bool(p.barcode),bool(profile.brand),bool(profile.primary_uom),profile.mrp>0,profile.dealer_price>0,profile.maximum_stock>=0]
            profile.data_quality_score=int(sum(checks)/len(checks)*100); profile.save(update_fields=['data_quality_score','updated_at']); updated+=1
        audit(request,'UPDATE','ProductMasterProfile','bulk',f'Recalculated quality for {updated} products')
        return JsonResponse({'updated':updated})
    product=_pick(m.Product.objects.filter(company=company),data.get('productId'))
    if not product:return JsonResponse({'detail':'Product not found.'},status=404)
    if action=='request-change':
        row=m.ProductChangeRequest.objects.create(company=company,product=product,change_type=data.get('changeType','Master data update'),requested_changes=data.get('changes',{}),reason=data.get('reason','Requested from PIM workbench'),requested_by=request.api_user)
        audit(request,'CREATE','ProductChangeRequest',row.id,f'Change requested for {product.sku}')
        return JsonResponse({'id':row.id,'status':row.status},status=201)
    if action in ['approve-change','reject-change']:
        row=m.ProductChangeRequest.objects.filter(company=company,pk=data.get('changeId')).select_related('product').first()
        if not row:return JsonResponse({'detail':'Change request not found.'},status=404)
        if request.api_user.profile.role not in ['OWNER','MANAGER','ACCOUNTANT']:return JsonResponse({'detail':'Approval requires owner, manager or accountant.'},status=403)
        row.status='Approved' if action=='approve-change' else 'Rejected'; row.approved_by=request.api_user; row.reviewed_at=timezone.now(); row.save(update_fields=['status','approved_by','reviewed_at'])
        if row.status=='Approved':
            direct={'hsn':'hsn_code','gst':'gst_rate','barcode':'barcode','name':'name','category':'category'}
            for k,field in direct.items():
                if k in row.requested_changes:setattr(row.product,field,row.requested_changes[k])
            row.product.save()
            profile,_=m.ProductMasterProfile.objects.get_or_create(company=company,product=row.product)
            for k in ['brand','manufacturer','primary_uom','purchase_uom','sales_uom','mrp','dealer_price','distributor_price','batch_required','serial_required','expiry_required']:
                if k in row.requested_changes:setattr(profile,k,row.requested_changes[k])
            profile.updated_by=request.api_user; profile.save()
        audit(request,'UPDATE','ProductChangeRequest',row.id,row.status)
        return JsonResponse({'id':row.id,'status':row.status})
    return JsonResponse({'detail':'Unsupported action.'},status=400)

# Phase 28
@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def traceability(request):
    denied=_guard(request,['OWNER','MANAGER','WAREHOUSE','SALES'])
    if denied:return denied
    company=request.company; today=timezone.localdate()
    if request.method=='GET':
        lots=m.InventoryLot.objects.filter(company=company).select_related('product','warehouse','supplier').order_by('expiry_date','product__name')
        serials=m.SerialUnit.objects.filter(company=company).select_related('product','warehouse','customer').order_by('-id')[:100]
        events=m.TraceabilityEvent.objects.filter(company=company).select_related('product','lot','serial').order_by('-created_at')[:60]
        expiring=lots.filter(expiry_date__isnull=False,expiry_date__lte=today+timedelta(days=60)).exclude(status__in=['Closed','Expired']).count()
        return JsonResponse({'summary':{'lots':lots.count(),'serials':m.SerialUnit.objects.filter(company=company).count(),'expiring':expiring,'recalls':lots.filter(status='Recall').count()},'lots':[{'id':x.id,'product':x.product.name,'sku':x.product.sku,'warehouse':x.warehouse.name,'lot':x.lot_no,'batch':x.batch_no,'expiry':_dt(x.expiry_date),'received':_money(x.received_qty),'available':_money(x.available_qty),'status':x.status} for x in lots[:100]],'serials':[{'id':x.id,'product':x.product.name,'serial':x.serial_no,'warehouse':x.warehouse.name if x.warehouse else '', 'status':x.status,'customer':x.customer.name if x.customer else '', 'warrantyUntil':_dt(x.warranty_until)} for x in serials],'events':[{'id':e.id,'product':e.product.name,'lot':e.lot.lot_no if e.lot else '', 'serial':e.serial.serial_no if e.serial else '', 'type':e.event_type,'reference':e.reference,'quantity':_money(e.quantity),'at':_dt(e.created_at)} for e in events]})
    data=_body(request); action=data.get('action','receive-lot')
    product=_pick(m.Product.objects.filter(company=company),data.get('productId')); warehouse=_pick(m.Warehouse.objects.filter(company=company),data.get('warehouseId'))
    if action=='receive-lot':
        if not product or not warehouse:return JsonResponse({'detail':'Product and warehouse required.'},status=400)
        supplier=_pick(m.Supplier.objects.filter(company=company),data.get('supplierId'))
        qty=Decimal(str(data.get('quantity',1)))
        row=m.InventoryLot.objects.create(company=company,product=product,warehouse=warehouse,supplier=supplier,lot_no=data.get('lotNo') or f"LOT-{timezone.now().strftime('%y%m%d%H%M%S')}",batch_no=data.get('batchNo',''),manufactured_on=data.get('manufacturedOn') or None,expiry_date=data.get('expiryDate') or None,received_qty=qty,available_qty=qty,unit_cost=data.get('unitCost',product.purchase_price))
        m.TraceabilityEvent.objects.create(company=company,product=product,lot=row,event_type='Received',reference=data.get('reference','Manual receipt'),quantity=qty,created_by=request.api_user)
        audit(request,'CREATE','InventoryLot',row.id,row.lot_no); return JsonResponse({'id':row.id,'lot':row.lot_no},status=201)
    if action=='add-serial':
        lot=_pick(m.InventoryLot.objects.filter(company=company),data.get('lotId'))
        product=product or (lot.product if lot else None); warehouse=warehouse or (lot.warehouse if lot else None)
        if not product:return JsonResponse({'detail':'Product required.'},status=400)
        serial=m.SerialUnit.objects.create(company=company,product=product,warehouse=warehouse,lot=lot,serial_no=data.get('serialNo') or f"SN{timezone.now().strftime('%y%m%d%H%M%S%f')}",warranty_until=data.get('warrantyUntil') or None)
        m.TraceabilityEvent.objects.create(company=company,product=product,lot=lot,serial=serial,event_type='Serialized',reference='PIM traceability',quantity=1,created_by=request.api_user)
        return JsonResponse({'id':serial.id,'serial':serial.serial_no},status=201)
    if action=='recall-lot':
        lot=m.InventoryLot.objects.filter(company=company,pk=data.get('lotId')).first()
        if not lot:return JsonResponse({'detail':'Lot not found.'},status=404)
        lot.status='Recall';lot.save(update_fields=['status']);m.TraceabilityEvent.objects.create(company=company,product=lot.product,lot=lot,event_type='Recall',reference=data.get('reason','Quality recall'),quantity=lot.available_qty,created_by=request.api_user);audit(request,'UPDATE','InventoryLot',lot.id,'Lot recalled');return JsonResponse({'id':lot.id,'status':lot.status})
    return JsonResponse({'detail':'Unsupported action.'},status=400)

# Phase 29
@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def treasury(request):
    denied=_guard(request,['OWNER','MANAGER','ACCOUNTANT'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        accounts=m.BankAccount.objects.filter(company=company).order_by('name')
        txns=m.BankTransaction.objects.filter(company=company).select_related('bank_account','matched_payment').order_by('-transaction_date','-id')[:100]
        forecasts=m.CashFlowForecast.objects.filter(company=company).order_by('forecast_date')[:30]
        balance=accounts.aggregate(v=Sum('current_balance'))['v'] or 0; unmatched=m.BankTransaction.objects.filter(company=company,matching_status='Unmatched').count()
        return JsonResponse({'summary':{'cashPosition':_money(balance),'unmatched':unmatched,'expectedInflow':_money(sum((x.expected_inflow for x in forecasts),Decimal('0'))),'expectedOutflow':_money(sum((x.expected_outflow for x in forecasts),Decimal('0')))},'accounts':[{'id':a.id,'name':a.name,'bank':a.bank_name,'last4':a.account_last4,'type':a.account_type,'balance':_money(a.current_balance)} for a in accounts],'transactions':[{'id':t.id,'date':_dt(t.transaction_date),'account':t.bank_account.name,'type':t.transaction_type,'amount':_money(t.amount),'reference':t.reference,'description':t.description,'status':t.matching_status,'matchedPayment':t.matched_payment.reference if t.matched_payment else ''} for t in txns],'forecast':[{'date':_dt(x.forecast_date),'inflow':_money(x.expected_inflow),'outflow':_money(x.expected_outflow),'balance':_money(x.projected_balance)} for x in forecasts]})
    data=_body(request); action=data.get('action','generate-forecast')
    if action=='generate-forecast':
        base=m.BankAccount.objects.filter(company=company).aggregate(v=Sum('current_balance'))['v'] or Decimal('0'); receivable=m.Customer.objects.filter(company=company).aggregate(v=Sum('outstanding'))['v'] or Decimal('0'); payable=m.Supplier.objects.filter(company=company).aggregate(v=Sum('outstanding'))['v'] or Decimal('0'); running=base
        for day in range(1,8):
            inflow=(receivable/Decimal('7')).quantize(Decimal('0.01')); outflow=(payable/Decimal('7')).quantize(Decimal('0.01')); running+=inflow-outflow
            m.CashFlowForecast.objects.update_or_create(company=company,forecast_date=timezone.localdate()+timedelta(days=day),defaults={'expected_inflow':inflow,'expected_outflow':outflow,'projected_balance':running,'source_snapshot':{'receivable':str(receivable),'payable':str(payable)}})
        audit(request,'UPDATE','CashFlowForecast','7-day','Generated 7-day cash forecast');return JsonResponse({'days':7,'projectedBalance':_money(running)})
    if action=='reconcile':
        matches=0
        for row in m.BankTransaction.objects.filter(company=company,matching_status='Unmatched'):
            payment=m.PaymentTransaction.objects.filter(company=company,reference=row.reference,amount=abs(row.amount)).first()
            if payment:row.matched_payment=payment;row.matching_status='Matched';row.save(update_fields=['matched_payment','matching_status']);matches+=1
        return JsonResponse({'matched':matches})
    account=_pick(m.BankAccount.objects.filter(company=company),data.get('accountId'))
    if action=='transaction' and account:
        amount=Decimal(str(data.get('amount',0))); row=m.BankTransaction.objects.create(company=company,bank_account=account,transaction_date=data.get('date') or timezone.localdate(),amount=amount,transaction_type=data.get('type','Credit'),reference=data.get('reference',''),description=data.get('description','Manual statement row'));account.current_balance+=amount if row.transaction_type=='Credit' else -amount;account.save(update_fields=['current_balance']);return JsonResponse({'id':row.id},status=201)
    return JsonResponse({'detail':'Unsupported action.'},status=400)

# Phase 30
@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def contracts(request):
    denied=_guard(request,['OWNER','MANAGER','SALES','ACCOUNTANT'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        agreements=m.RateAgreement.objects.filter(company=company).select_related('customer').prefetch_related('items__product').order_by('-start_date')
        tenders=m.Tender.objects.filter(company=company).select_related('customer').order_by('due_date')
        return JsonResponse({'summary':{'active':agreements.filter(status='Active').count(),'contractValue':_money(agreements.aggregate(v=Sum('minimum_monthly_purchase'))['v'] or 0),'openTenders':tenders.exclude(status__in=['Won','Lost','Cancelled']).count(),'tenderValue':_money(tenders.exclude(status__in=['Lost','Cancelled']).aggregate(v=Sum('expected_value'))['v'] or 0)},'agreements':[{'id':a.id,'agreementNo':a.agreement_no,'customer':a.customer.name,'title':a.title,'start':_dt(a.start_date),'end':_dt(a.end_date),'status':a.status,'minimumMonthly':_money(a.minimum_monthly_purchase),'creditDays':a.credit_days,'items':[{'product':i.product.name,'sku':i.product.sku,'rate':_money(i.rate),'minQty':_money(i.minimum_qty),'escalation':_money(i.escalation_percent)} for i in a.items.all()]} for a in agreements],'tenders':[{'id':t.id,'tenderNo':t.tender_no,'customer':t.customer.name if t.customer else '', 'title':t.title,'due':_dt(t.due_date),'value':_money(t.expected_value),'status':t.status} for t in tenders]})
    data=_body(request); action=data.get('action','agreement')
    customer=_pick(m.Customer.objects.filter(company=company),data.get('customerId'))
    if action=='agreement':
        if not customer:return JsonResponse({'detail':'Customer required.'},status=400)
        a=m.RateAgreement.objects.create(company=company,customer=customer,agreement_no=data.get('agreementNo') or f"AGR-{timezone.now().strftime('%y%m%d%H%M%S')}",title=data.get('title','B2B Rate Agreement'),start_date=data.get('start') or timezone.localdate(),end_date=data.get('end') or timezone.localdate()+timedelta(days=180),minimum_monthly_purchase=data.get('minimumMonthly',0),credit_days=data.get('creditDays',30),notes=data.get('notes',''),created_by=request.api_user);return JsonResponse({'id':a.id,'agreementNo':a.agreement_no},status=201)
    if action=='add-item':
        a=m.RateAgreement.objects.filter(company=company,pk=data.get('agreementId')).first();p=_pick(m.Product.objects.filter(company=company),data.get('productId'))
        if not a or not p:return JsonResponse({'detail':'Agreement and product required.'},status=400)
        row,_=m.RateAgreementItem.objects.update_or_create(agreement=a,product=p,defaults={'rate':data.get('rate',p.sell_price),'minimum_qty':data.get('minimumQty',1),'maximum_qty':data.get('maximumQty') or None,'escalation_percent':data.get('escalation',0)});return JsonResponse({'id':row.id},status=201)
    if action=='tender':
        t=m.Tender.objects.create(company=company,customer=customer,tender_no=data.get('tenderNo') or f"TND-{timezone.now().strftime('%y%m%d%H%M%S')}",title=data.get('title','New tender opportunity'),due_date=data.get('dueDate') or timezone.localdate()+timedelta(days=14),expected_value=data.get('value',0),terms=data.get('terms',{}));return JsonResponse({'id':t.id,'tenderNo':t.tender_no},status=201)
    return JsonResponse({'detail':'Unsupported action.'},status=400)

# Phase 31
@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def quality(request):
    denied=_guard(request,['OWNER','MANAGER','WAREHOUSE'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        rows_q=m.QualityInspection.objects.filter(company=company); q_q=m.QuarantineStock.objects.filter(company=company)
        rows=rows_q.select_related('product','warehouse','supplier').order_by('-created_at')[:100]; q=q_q.select_related('product','warehouse','inspection').order_by('-id')[:100]
        rejected=rows_q.aggregate(v=Sum('quantity_rejected'))['v'] or 0; quarantined=q_q.filter(status='Quarantined').aggregate(v=Sum('quantity'))['v'] or 0
        return JsonResponse({'summary':{'pending':rows_q.filter(status='Pending').count(),'rejectedQty':_money(rejected),'quarantineQty':_money(quarantined),'completed':rows_q.filter(status='Completed').count()},'inspections':[{'id':x.id,'inspectionNo':x.inspection_no,'type':x.inspection_type,'product':x.product.name,'warehouse':x.warehouse.name,'supplier':x.supplier.name if x.supplier else '', 'received':_money(x.quantity_received),'inspected':_money(x.quantity_inspected),'passed':_money(x.quantity_passed),'rejected':_money(x.quantity_rejected),'quarantine':_money(x.quantity_quarantined),'status':x.status} for x in rows],'quarantine':[{'id':x.id,'inspection':x.inspection.inspection_no,'product':x.product.name,'warehouse':x.warehouse.name,'quantity':_money(x.quantity),'reason':x.reason,'status':x.status} for x in q]})
    data=_body(request);action=data.get('action','inspection')
    if action=='inspection':
        p=_pick(m.Product.objects.filter(company=company),data.get('productId'));w=_pick(m.Warehouse.objects.filter(company=company),data.get('warehouseId'));s=_pick(m.Supplier.objects.filter(company=company),data.get('supplierId'))
        if not p or not w:return JsonResponse({'detail':'Product and warehouse required.'},status=400)
        row=m.QualityInspection.objects.create(company=company,inspection_no=data.get('inspectionNo') or f"QC-{timezone.now().strftime('%y%m%d%H%M%S')}",inspection_type=data.get('type','Incoming'),product=p,warehouse=w,supplier=s,quantity_received=data.get('quantity',0),status='Pending',checklist=data.get('checklist',{}));return JsonResponse({'id':row.id,'inspectionNo':row.inspection_no},status=201)
    row=m.QualityInspection.objects.filter(company=company,pk=data.get('inspectionId')).select_related('product','warehouse').first()
    if not row:return JsonResponse({'detail':'Inspection not found.'},status=404)
    if action=='complete':
        row.quantity_inspected=data.get('inspected',row.quantity_received);row.quantity_passed=data.get('passed',row.quantity_inspected);row.quantity_rejected=data.get('rejected',0);row.quantity_quarantined=data.get('quarantined',row.quantity_rejected);row.status='Completed';row.inspected_by=request.api_user;row.inspected_at=timezone.now();row.notes=data.get('notes','');row.save()
        if Decimal(str(row.quantity_quarantined))>0:m.QuarantineStock.objects.create(company=company,inspection=row,product=row.product,warehouse=row.warehouse,quantity=row.quantity_quarantined,reason=data.get('reason','QC hold'))
        audit(request,'UPDATE','QualityInspection',row.id,'Inspection completed');return JsonResponse({'id':row.id,'status':row.status})
    if action=='release':
        q=m.QuarantineStock.objects.filter(company=company,pk=data.get('quarantineId')).first()
        if not q:return JsonResponse({'detail':'Quarantine row not found.'},status=404)
        q.status='Released';q.released_at=timezone.now();q.save(update_fields=['status','released_at']);return JsonResponse({'id':q.id,'status':q.status})
    return JsonResponse({'detail':'Unsupported action.'},status=400)

# Phase 32
@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def supply_planning(request):
    denied=_guard(request,['OWNER','MANAGER','WAREHOUSE'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        scenario_q=m.SupplyPlanScenario.objects.filter(company=company); plan_q=m.ReplenishmentPlan.objects.filter(company=company)
        scenarios=scenario_q.order_by('-created_at')[:30]
        plans=plan_q.select_related('scenario','product','from_warehouse','to_warehouse').order_by('-generated_at')[:120]
        return JsonResponse({'summary':{'scenarios':scenario_q.count(),'recommendedPurchase':_money(plan_q.filter(status='Recommended').aggregate(v=Sum('purchase_qty'))['v'] or 0),'recommendedTransfer':_money(plan_q.filter(status='Recommended').aggregate(v=Sum('transfer_qty'))['v'] or 0),'products':plan_q.values('product_id').distinct().count()},'scenarios':[{'id':x.id,'name':x.name,'horizon':x.horizon_days,'demandMultiplier':_money(x.demand_multiplier),'supplierDelay':x.supplier_delay_days,'status':x.status} for x in scenarios],'plans':[{'id':x.id,'scenario':x.scenario.name,'product':x.product.name,'sku':x.product.sku,'fromWarehouse':x.from_warehouse.name if x.from_warehouse else '', 'toWarehouse':x.to_warehouse.name if x.to_warehouse else '', 'demand':_money(x.forecast_demand),'stock':_money(x.available_stock),'transfer':_money(x.transfer_qty),'purchase':_money(x.purchase_qty),'recommendation':x.recommendation,'status':x.status} for x in plans]})
    data=_body(request); action=data.get('action','generate')
    if action=='generate':
        scenario=m.SupplyPlanScenario.objects.create(company=company,name=data.get('name','30-day base plan'),horizon_days=int(data.get('horizon',30)),demand_multiplier=Decimal(str(data.get('demandMultiplier',1))),supplier_delay_days=int(data.get('supplierDelay',0)),status='Generated',notes=data.get('notes',''),created_by=request.api_user)
        warehouses=list(m.Warehouse.objects.filter(company=company,is_active=True)); generated=0
        for p in m.Product.objects.filter(company=company,is_active=True)[:50]:
            balances=list(m.StockBalance.objects.filter(product=p,warehouse__company=company).select_related('warehouse')); total=sum((b.quantity-b.reserved for b in balances),Decimal('0')); demand=max(p.reorder_level*Decimal(str(scenario.demand_multiplier))*Decimal('2'),Decimal('0')); safety=p.reorder_level; need=max(demand+safety-total,Decimal('0'))
            target=warehouses[0] if warehouses else None; source=max(balances,key=lambda b:b.quantity).warehouse if balances else None; transfer=Decimal('0')
            if source and target and source.id!=target.id and total>need: transfer=min(need,total/Decimal('4'))
            purchase=max(need-transfer,Decimal('0'))
            m.ReplenishmentPlan.objects.create(company=company,scenario=scenario,product=p,from_warehouse=source if transfer else None,to_warehouse=target,forecast_demand=demand,available_stock=total,safety_stock=safety,transfer_qty=transfer,purchase_qty=purchase,recommendation=('Transfer then purchase' if transfer and purchase else 'Transfer stock' if transfer else 'Purchase stock' if purchase else 'Stock sufficient'))
            generated+=1
        audit(request,'CREATE','SupplyPlanScenario',scenario.id,f'Generated {generated} replenishment lines');return JsonResponse({'id':scenario.id,'plans':generated},status=201)
    row=m.ReplenishmentPlan.objects.filter(company=company,pk=data.get('planId')).first()
    if action=='approve' and row:row.status='Approved';row.save(update_fields=['status']);return JsonResponse({'id':row.id,'status':row.status})
    return JsonResponse({'detail':'Unsupported action.'},status=400)

# Phase 33
@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def service_rma(request):
    denied=_guard(request,['OWNER','MANAGER','SALES','WAREHOUSE'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        ticket_q=m.ServiceTicket.objects.filter(company=company); rma_q=m.RMA.objects.filter(company=company)
        tickets=ticket_q.select_related('customer','product','serial','technician').order_by('-created_at')[:100]
        rmas=rma_q.select_related('ticket','replacement_product').order_by('-created_at')[:100]
        return JsonResponse({'summary':{'open':ticket_q.exclude(status__in=['Closed','Cancelled']).count(),'warranty':ticket_q.filter(warranty_valid=True).count(),'rmas':rma_q.count(),'claimValue':_money(rma_q.aggregate(v=Sum('manufacturer_claim_amount'))['v'] or 0)},'tickets':[{'id':x.id,'ticketNo':x.ticket_no,'customer':x.customer.name,'product':x.product.name,'serial':x.serial.serial_no if x.serial else '', 'complaint':x.complaint,'status':x.status,'warranty':x.warranty_valid,'technician':x.technician.get_full_name() if x.technician else '', 'diagnosis':x.diagnosis} for x in tickets],'rmas':[{'id':x.id,'rmaNo':x.rma_no,'ticket':x.ticket.ticket_no,'action':x.action,'status':x.status,'cost':_money(x.cost),'claimAmount':_money(x.manufacturer_claim_amount),'claimStatus':x.manufacturer_claim_status} for x in rmas]})
    data=_body(request); action=data.get('action','ticket')
    if action=='ticket':
        c=_pick(m.Customer.objects.filter(company=company),data.get('customerId'));p=_pick(m.Product.objects.filter(company=company),data.get('productId'));serial=_pick(m.SerialUnit.objects.filter(company=company),data.get('serialId'))
        if not c or not p:return JsonResponse({'detail':'Customer and product required.'},status=400)
        until=serial.warranty_until if serial else None;valid=bool(until and until>=timezone.localdate())
        row=m.ServiceTicket.objects.create(company=company,ticket_no=data.get('ticketNo') or f"SRV-{timezone.now().strftime('%y%m%d%H%M%S')}",customer=c,product=p,serial=serial,complaint=data.get('complaint','Service request'),warranty_valid=valid,warranty_until=until,status='Open');return JsonResponse({'id':row.id,'ticketNo':row.ticket_no,'warranty':row.warranty_valid},status=201)
    ticket=m.ServiceTicket.objects.filter(company=company,pk=data.get('ticketId')).first()
    if not ticket:return JsonResponse({'detail':'Service ticket not found.'},status=404)
    if action=='diagnose':ticket.diagnosis=data.get('diagnosis','Inspection completed');ticket.status=data.get('status','In Service');ticket.technician=request.api_user;ticket.save(update_fields=['diagnosis','status','technician']);return JsonResponse({'id':ticket.id,'status':ticket.status})
    if action=='rma':
        row=m.RMA.objects.create(company=company,rma_no=data.get('rmaNo') or f"RMA-{timezone.now().strftime('%y%m%d%H%M%S')}",ticket=ticket,action=data.get('rmaAction','Repair'),status='Created',cost=data.get('cost',0),manufacturer_claim_amount=data.get('claimAmount',0),manufacturer_claim_status='Pending' if Decimal(str(data.get('claimAmount',0)))>0 else '')
        return JsonResponse({'id':row.id,'rmaNo':row.rma_no},status=201)
    if action=='close':ticket.status='Closed';ticket.resolution=data.get('resolution','Resolved');ticket.closed_at=timezone.now();ticket.save(update_fields=['status','resolution','closed_at']);return JsonResponse({'id':ticket.id,'status':ticket.status})
    return JsonResponse({'detail':'Unsupported action.'},status=400)

# Phase 34
@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def expenses(request):
    denied=_guard(request,['OWNER','MANAGER','SALES','WAREHOUSE','ACCOUNTANT'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        claim_q=m.ExpenseClaim.objects.filter(company=company); claims=claim_q.select_related('employee','branch','approved_by').order_by('-expense_date','-id')[:100];accounts=m.PettyCashAccount.objects.filter(company=company).select_related('branch').order_by('name');txns=m.PettyCashTransaction.objects.filter(account__company=company).select_related('account','claim').order_by('-transaction_date','-id')[:60]
        return JsonResponse({'summary':{'submitted':_money(claim_q.filter(status='Submitted').aggregate(v=Sum('amount'))['v'] or 0),'approved':_money(claim_q.filter(status='Approved').aggregate(v=Sum('amount'))['v'] or 0),'pettyCash':_money(accounts.aggregate(v=Sum('balance'))['v'] or 0),'claims':claim_q.count()},'claims':[{'id':x.id,'claimNo':x.claim_no,'employee':x.employee.get_full_name() or x.employee.username,'branch':x.branch.name if x.branch else '', 'category':x.category,'amount':_money(x.amount),'date':_dt(x.expense_date),'method':x.payment_method,'status':x.status,'description':x.description} for x in claims],'accounts':[{'id':x.id,'name':x.name,'branch':x.branch.name if x.branch else '', 'balance':_money(x.balance)} for x in accounts],'transactions':[{'id':x.id,'account':x.account.name,'date':_dt(x.transaction_date),'type':x.transaction_type,'amount':_money(x.amount),'claim':x.claim.claim_no if x.claim else '', 'note':x.note} for x in txns]})
    data=_body(request); action=data.get('action','submit')
    if action=='submit':
        row=m.ExpenseClaim.objects.create(company=company,claim_no=data.get('claimNo') or f"EXP-{timezone.now().strftime('%y%m%d%H%M%S')}",employee=request.api_user,branch=request.api_user.profile.branch,category=data.get('category','Travel'),amount=data.get('amount',0),expense_date=data.get('date') or timezone.localdate(),payment_method=data.get('method','Cash'),description=data.get('description',''),receipt_url=data.get('receiptUrl',''));return JsonResponse({'id':row.id,'claimNo':row.claim_no},status=201)
    claim=m.ExpenseClaim.objects.filter(company=company,pk=data.get('claimId')).first()
    if action in ['approve','reject'] and claim:
        if request.api_user.profile.role not in ['OWNER','MANAGER','ACCOUNTANT']:return JsonResponse({'detail':'Approval requires owner, manager or accountant.'},status=403)
        claim.status='Approved' if action=='approve' else 'Rejected';claim.approved_by=request.api_user;claim.approved_at=timezone.now();claim.save(update_fields=['status','approved_by','approved_at']);return JsonResponse({'id':claim.id,'status':claim.status})
    if action=='pay' and claim:
        account=_pick(m.PettyCashAccount.objects.filter(company=company),data.get('accountId'))
        if not account:return JsonResponse({'detail':'Petty cash account required.'},status=400)
        if account.balance<claim.amount:return JsonResponse({'detail':'Insufficient petty cash balance.'},status=400)
        m.PettyCashTransaction.objects.create(account=account,claim=claim,transaction_date=timezone.localdate(),transaction_type='Debit',amount=claim.amount,note=f'Paid {claim.claim_no}',created_by=request.api_user);account.balance-=claim.amount;account.save(update_fields=['balance']);claim.status='Paid';claim.paid_at=timezone.now();claim.save(update_fields=['status','paid_at']);return JsonResponse({'id':claim.id,'status':claim.status,'balance':_money(account.balance)})
    return JsonResponse({'detail':'Unsupported action.'},status=400)

# Phase 35
@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def report_builder(request):
    denied=_guard(request,['OWNER','MANAGER','ACCOUNTANT'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        defs=m.ReportDefinition.objects.filter(company=company).select_related('owner').order_by('-updated_at'); schedules=m.ScheduledReport.objects.filter(company=company).select_related('report').order_by('report__name'); run_q=m.ReportRun.objects.filter(report__company=company); runs=run_q.select_related('report').order_by('-created_at')[:40]
        return JsonResponse({'summary':{'reports':defs.count(),'scheduled':schedules.filter(is_active=True).count(),'runs':run_q.count(),'failed':run_q.filter(status='Failed').count()},'reports':[{'id':x.id,'name':x.name,'source':x.data_source,'dimensions':x.dimensions,'measures':x.measures,'filters':x.filters,'shared':x.is_shared,'owner':x.owner.get_full_name() if x.owner else ''} for x in defs],'schedules':[{'id':x.id,'report':x.report.name,'frequency':x.frequency,'time':str(x.delivery_time) if x.delivery_time else '', 'recipients':x.recipients,'format':x.output_format,'active':x.is_active,'nextRun':_dt(x.next_run_at)} for x in schedules],'runs':[{'id':x.id,'report':x.report.name,'status':x.status,'rows':x.row_count,'createdAt':_dt(x.created_at),'error':x.error} for x in runs]})
    data=_body(request); action=data.get('action','create-report')
    if action=='create-report':
        row=m.ReportDefinition.objects.create(company=company,name=data.get('name','Custom sales report'),data_source=data.get('source','Sales'),dimensions=data.get('dimensions',['Customer','Product']),measures=data.get('measures',['Revenue','Quantity']),filters=data.get('filters',{}),group_by=data.get('groupBy',[]),owner=request.api_user,is_shared=bool(data.get('shared',False)));return JsonResponse({'id':row.id},status=201)
    report=m.ReportDefinition.objects.filter(company=company,pk=data.get('reportId')).first()
    if not report:return JsonResponse({'detail':'Report not found.'},status=404)
    if action=='schedule':
        row=m.ScheduledReport.objects.create(company=company,report=report,frequency=data.get('frequency','Weekly'),delivery_time=data.get('time') or None,weekdays=data.get('weekdays',[]),recipients=data.get('recipients',[company.email] if company.email else []),output_format=data.get('format','XLSX'),next_run_at=timezone.now()+timedelta(days=1));return JsonResponse({'id':row.id},status=201)
    if action=='run':
        source_counts={'Sales':m.Order.objects.filter(company=company).count(),'Customers':m.Customer.objects.filter(company=company).count(),'Inventory':m.StockBalance.objects.filter(warehouse__company=company).count(),'Purchases':m.PurchaseOrder.objects.filter(company=company).count()};row=m.ReportRun.objects.create(report=report,status='Completed',row_count=source_counts.get(report.data_source,0),started_at=timezone.now(),finished_at=timezone.now());return JsonResponse({'id':row.id,'status':row.status,'rows':row.row_count},status=201)
    return JsonResponse({'detail':'Unsupported action.'},status=400)

# Phase 36
@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def operations_center(request):
    denied=_guard(request,['OWNER','MANAGER'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        health=m.ServiceHealth.objects.filter(company=company).order_by('category','service_name');job_q=m.BackgroundJob.objects.filter(company=company);hook_q=m.WebhookReplay.objects.filter(company=company);jobs=job_q.order_by('-created_at')[:100];hooks=hook_q.order_by('-created_at')[:100];alerts=m.AlertPolicy.objects.filter(company=company).order_by('name')
        return JsonResponse({'summary':{'healthy':health.filter(status='Healthy').count(),'degraded':health.exclude(status='Healthy').count(),'failedJobs':job_q.filter(status='Failed').count(),'failedWebhooks':hook_q.filter(status='Failed').count()},'services':[{'id':x.id,'service':x.service_name,'category':x.category,'status':x.status,'latency':x.latency_ms,'message':x.message,'checkedAt':_dt(x.checked_at)} for x in health],'jobs':[{'id':x.id,'type':x.job_type,'key':x.job_key,'status':x.status,'attempts':x.attempts,'error':x.last_error,'scheduledAt':_dt(x.scheduled_at)} for x in jobs],'webhooks':[{'id':x.id,'source':x.source,'eventId':x.event_id,'status':x.status,'attempts':x.attempts,'error':x.last_error} for x in hooks],'alerts':[{'id':x.id,'name':x.name,'condition':x.condition,'threshold':_money(x.threshold),'channels':x.channels,'active':x.is_active} for x in alerts]})
    data=_body(request); action=data.get('action','heartbeat')
    if action=='heartbeat':
        defaults=[('Django API','Internal','Healthy',42),('PostgreSQL','Internal','Healthy',18),('Redis / Queue','Internal','Healthy',8),('WhatsApp','Provider','Healthy',110),('GST IRP','Provider','Degraded',380),('Payment Provider','Provider','Healthy',142),('ONDC Adapter','Provider','Healthy',190)]
        for name,category,status,latency in defaults:m.ServiceHealth.objects.update_or_create(company=company,service_name=name,defaults={'category':category,'status':status,'latency_ms':latency,'message':'Automated release heartbeat'})
        return JsonResponse({'checked':len(defaults)})
    if action=='retry-job':
        row=m.BackgroundJob.objects.filter(company=company,pk=data.get('jobId')).first()
        if not row:return JsonResponse({'detail':'Job not found.'},status=404)
        row.attempts+=1;row.status='Queued';row.last_error='';row.scheduled_at=timezone.now();row.save(update_fields=['attempts','status','last_error','scheduled_at']);return JsonResponse({'id':row.id,'status':row.status,'attempts':row.attempts})
    if action=='replay-webhook':
        row=m.WebhookReplay.objects.filter(company=company,pk=data.get('webhookId')).first()
        if not row:return JsonResponse({'detail':'Webhook row not found.'},status=404)
        row.attempts+=1;row.status='Queued';row.last_error='';row.save(update_fields=['attempts','status','last_error','updated_at']);return JsonResponse({'id':row.id,'status':row.status})
    if action=='alert':
        row=m.AlertPolicy.objects.create(company=company,name=data.get('name','Failed jobs alert'),condition=data.get('condition','failed_jobs'),threshold=data.get('threshold',1),channels=data.get('channels',['email']),is_active=True);return JsonResponse({'id':row.id},status=201)
    return JsonResponse({'detail':'Unsupported action.'},status=400)
