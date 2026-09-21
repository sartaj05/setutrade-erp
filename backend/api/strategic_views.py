import json, secrets, hashlib
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count, Avg, F
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .auth import api_auth_required
from . import models as m
from .services import audit, notify

def _body(request):
    try: return json.loads(request.body or '{}')
    except json.JSONDecodeError: return {}
def _money(v): return float(v or 0)
def _dt(v): return v.isoformat() if v else None
def _guard(request, roles):
    return None if request.api_user.profile.role in roles else JsonResponse({'detail':'You do not have access to this module.'},status=403)

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def crm(request):
    denied=_guard(request,['OWNER','MANAGER','SALES'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        leads=m.CRMLead.objects.filter(company=company).select_related('owner').order_by('-updated_at')[:100]
        stage=list(m.CRMLead.objects.filter(company=company).values('status').annotate(count=Count('id'),value=Sum('estimated_value')).order_by('status'))
        activities=m.CRMActivity.objects.filter(company=company).select_related('lead','created_by').order_by('-created_at')[:30]
        won=m.CRMLead.objects.filter(company=company,status='Won').aggregate(v=Sum('estimated_value'))['v'] or 0
        total=m.CRMLead.objects.filter(company=company).count(); won_count=m.CRMLead.objects.filter(company=company,status='Won').count()
        return JsonResponse({'summary':{'pipelineValue':_money(m.CRMLead.objects.filter(company=company).exclude(status__in=['Won','Lost']).aggregate(v=Sum('estimated_value'))['v'] or 0),'wonValue':_money(won),'conversion':round((won_count/total*100),1) if total else 0},'stages':[{'status':x['status'],'count':x['count'],'value':_money(x['value'])} for x in stage],'leads':[{'id':x.id,'leadNo':x.lead_no,'name':x.name,'business':x.business_name,'status':x.status,'source':x.source,'territory':x.territory,'value':_money(x.estimated_value),'close':_dt(x.expected_close),'owner':x.owner.get_full_name() if x.owner else ''} for x in leads],'activities':[{'id':a.id,'lead':a.lead.business_name or a.lead.name,'type':a.activity_type,'note':a.note,'next':_dt(a.next_follow_up),'completed':a.completed} for a in activities]})
    data=_body(request); action=data.get('action','lead')
    if action=='lead':
        lead=m.CRMLead.objects.create(company=company,lead_no=data.get('leadNo') or f"LEAD-{timezone.now().strftime('%y%m%d%H%M%S%f')}",name=data.get('name','New Lead'),business_name=data.get('business',''),phone=data.get('phone',''),email=data.get('email',''),source=data.get('source','Referral'),territory=data.get('territory',''),estimated_value=data.get('value',0),expected_close=data.get('expectedClose') or None,owner=request.api_user)
        audit(request,'CREATE','CRMLead',lead.id,f'Created lead {lead.lead_no}')
        return JsonResponse({'id':lead.id,'leadNo':lead.lead_no},status=201)
    lead=m.CRMLead.objects.filter(company=company,pk=data.get('leadId')).first()
    if not lead: return JsonResponse({'detail':'Lead not found.'},status=404)
    if action=='stage':
        lead.status=data.get('status',lead.status); lead.lost_reason=data.get('lostReason',''); lead.save(update_fields=['status','lost_reason','updated_at']); audit(request,'UPDATE','CRMLead',lead.id,f'Moved lead to {lead.status}'); return JsonResponse({'id':lead.id,'status':lead.status})
    if action=='activity':
        row=m.CRMActivity.objects.create(company=company,lead=lead,activity_type=data.get('type','Call'),note=data.get('note','Follow-up'),next_follow_up=data.get('nextFollowUp') or None,created_by=request.api_user); return JsonResponse({'id':row.id},status=201)
    return JsonResponse({'detail':'Unsupported action.'},status=400)

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def schemes(request):
    denied=_guard(request,['OWNER','MANAGER','ACCOUNTANT'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        schemes=m.ManufacturerScheme.objects.filter(company=company).select_related('supplier').order_by('-end_date')
        claims=m.SchemeClaim.objects.filter(company=company).select_related('scheme','scheme__supplier').order_by('-id')
        accrued=claims.exclude(status__in=['Rejected','Settled']).aggregate(v=Sum('claim_amount'))['v'] or 0
        return JsonResponse({'summary':{'active':schemes.filter(is_active=True).count(),'accrued':_money(accrued),'claims':claims.count()},'schemes':[{'id':x.id,'name':x.name,'supplier':x.supplier.name,'type':x.scheme_type,'start':_dt(x.start_date),'end':_dt(x.end_date),'target':_money(x.target_value),'rebate':_money(x.rebate_percent),'active':x.is_active} for x in schemes],'claims':[{'id':x.id,'claimNo':x.claim_no,'scheme':x.scheme.name,'supplier':x.scheme.supplier.name,'eligible':_money(x.eligible_value),'amount':_money(x.claim_amount),'status':x.status} for x in claims]})
    data=_body(request); action=data.get('action')
    if action=='create-scheme':
        supplier=m.Supplier.objects.filter(company=company,pk=data.get('supplierId')).first() or m.Supplier.objects.filter(company=company).first()
        if not supplier:return JsonResponse({'detail':'Supplier required.'},status=400)
        row=m.ManufacturerScheme.objects.create(company=company,supplier=supplier,name=data.get('name','Quarterly growth rebate'),scheme_type=data.get('type','Rebate'),start_date=data.get('start') or timezone.localdate(),end_date=data.get('end') or timezone.localdate(),target_value=data.get('target',0),rebate_percent=data.get('rebate',1.5),rules=data.get('rules',{})); audit(request,'CREATE','ManufacturerScheme',row.id,row.name); return JsonResponse({'id':row.id},status=201)
    scheme=m.ManufacturerScheme.objects.filter(company=company,pk=data.get('schemeId')).select_related('supplier').first()
    if not scheme:return JsonResponse({'detail':'Scheme not found.'},status=404)
    eligible=Decimal(str(data.get('eligibleValue',0))); amount=(eligible*scheme.rebate_percent/Decimal('100')).quantize(Decimal('0.01'))
    claim=m.SchemeClaim.objects.create(company=company,scheme=scheme,claim_no=f"CLM-{timezone.now().strftime('%y%m%d%H%M%S%f')}",period_from=data.get('from') or scheme.start_date,period_to=data.get('to') or scheme.end_date,eligible_value=eligible,claim_amount=amount,status='Submitted' if action=='submit-claim' else 'Accrued',submitted_at=timezone.now() if action=='submit-claim' else None,evidence=data.get('evidence',[])); audit(request,'CREATE','SchemeClaim',claim.id,claim.claim_no); return JsonResponse({'id':claim.id,'claimNo':claim.claim_no,'amount':_money(claim.claim_amount),'status':claim.status},status=201)

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def gst_cockpit(request):
    denied=_guard(request,['OWNER','MANAGER','ACCOUNTANT'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        rows=m.GSTReconciliationItem.objects.filter(company=company).select_related('supplier').order_by('-invoice_date','-id')
        return JsonResponse({'summary':{'matched':rows.filter(status='Matched').count(),'mismatch':rows.filter(status='Mismatch').count(),'missing':rows.filter(status='Missing').count(),'taxDifference':_money(rows.exclude(status='Matched').aggregate(v=Sum('difference'))['v'] or 0)},'items':[{'id':x.id,'invoiceNo':x.invoice_no,'supplier':x.supplier.name if x.supplier else 'Unknown','gstin':x.gstin,'booksTax':_money(x.books_tax),'portalTax':_money(x.portal_tax),'difference':_money(x.difference),'status':x.status,'source':x.source} for x in rows]})
    data=_body(request); action=data.get('action','import')
    if action=='resolve':
        row=m.GSTReconciliationItem.objects.filter(company=company,pk=data.get('id')).first()
        if not row:return JsonResponse({'detail':'Reconciliation item not found.'},status=404)
        row.status='Resolved';row.resolution_note=data.get('note','Reviewed and resolved');row.save(update_fields=['status','resolution_note','updated_at']);audit(request,'UPDATE','GSTReconciliationItem',row.id,row.resolution_note);return JsonResponse({'id':row.id,'status':row.status})
    supplier=m.Supplier.objects.filter(company=company,pk=data.get('supplierId')).first() or m.Supplier.objects.filter(company=company).first()
    books=Decimal(str(data.get('booksTax',18440)));portal=Decimal(str(data.get('portalTax',18440)));diff=books-portal;status='Matched' if abs(diff)<Decimal('0.01') else 'Mismatch'
    row,_=m.GSTReconciliationItem.objects.update_or_create(company=company,invoice_no=data.get('invoiceNo') or f"IMS-{timezone.now().strftime('%y%m%d%H%M%S%f')}",source=data.get('source','IMS'),defaults={'supplier':supplier,'invoice_date':data.get('date') or timezone.localdate(),'gstin':data.get('gstin',''),'books_taxable':data.get('booksTaxable',0),'books_tax':books,'portal_taxable':data.get('portalTaxable',0),'portal_tax':portal,'difference':diff,'status':status});return JsonResponse({'id':row.id,'status':row.status,'difference':_money(row.difference)},status=201)

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def procurement_intelligence(request):
    denied=_guard(request,['OWNER','MANAGER','WAREHOUSE'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        scores=m.VendorScorecard.objects.filter(company=company).select_related('supplier').order_by('-overall_score')
        recs=m.ProcurementRecommendation.objects.filter(company=company).select_related('product','supplier').order_by('status','product__name')
        return JsonResponse({'summary':{'vendors':scores.count(),'openRecommendations':recs.filter(status='Open').count(),'recommendedSpend':_money(sum((x.recommended_qty*x.expected_unit_cost for x in recs.filter(status='Open')),Decimal('0')))},'vendors':[{'id':x.id,'supplier':x.supplier.name,'score':_money(x.overall_score),'fillRate':_money(x.fill_rate),'onTime':_money(x.on_time_rate),'quality':_money(x.quality_score),'leadDays':_money(x.avg_lead_days)} for x in scores],'recommendations':[{'id':x.id,'product':x.product.name,'sku':x.product.sku,'supplier':x.supplier.name,'qty':_money(x.recommended_qty),'unitCost':_money(x.expected_unit_cost),'leadDays':x.expected_lead_days,'reason':x.reason,'status':x.status} for x in recs]})
    data=_body(request); action=data.get('action','recalculate')
    if action=='approve':
        rec=m.ProcurementRecommendation.objects.filter(company=company,pk=data.get('id')).first()
        if not rec:return JsonResponse({'detail':'Recommendation not found.'},status=404)
        rec.status='Approved';rec.save(update_fields=['status']);audit(request,'APPROVE','ProcurementRecommendation',rec.id,'Approved procurement recommendation');return JsonResponse({'id':rec.id,'status':rec.status})
    suppliers=list(m.Supplier.objects.filter(company=company,is_active=True)); products=m.Product.objects.filter(company=company,is_active=True,stock__lte=F('reorder_level'))
    if not suppliers:return JsonResponse({'detail':'Add a supplier before recalculating.'},status=400)
    created=0
    for i,p in enumerate(products):
        supplier=suppliers[i%len(suppliers)]; score, _=m.VendorScorecard.objects.get_or_create(company=company,supplier=supplier,defaults={'price_score':84,'fill_rate':96,'on_time_rate':92,'quality_score':95,'payment_term_score':80,'overall_score':90,'avg_lead_days':5})
        qty=max(Decimal('1'),p.reorder_level*Decimal('2')-p.stock); m.ProcurementRecommendation.objects.update_or_create(company=company,product=p,supplier=supplier,defaults={'recommended_qty':qty,'expected_unit_cost':p.purchase_price,'expected_lead_days':int(score.avg_lead_days or 5),'reason':f'Stock {p.stock} is at/below reorder level {p.reorder_level}. Vendor score {score.overall_score}.','status':'Open'});created+=1
    return JsonResponse({'created':created})

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def fleet_routes(request):
    denied=_guard(request,['OWNER','MANAGER','SALES'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        vehicles=m.FleetVehicle.objects.filter(company=company,is_active=True).order_by('vehicle_no')
        routes=m.RoutePlan.objects.filter(company=company).select_related('vehicle','warehouse').prefetch_related('stops__order__customer').order_by('-route_date','-id')
        return JsonResponse({'summary':{'vehicles':vehicles.count(),'planned':routes.exclude(status='Complete').count(),'km':_money(routes.aggregate(v=Sum('estimated_km'))['v'] or 0),'cost':_money(routes.aggregate(v=Sum('estimated_cost'))['v'] or 0)},'vehicles':[{'id':v.id,'vehicleNo':v.vehicle_no,'type':v.vehicle_type,'capacityKg':_money(v.capacity_kg),'driver':v.driver_name,'costPerKm':_money(v.cost_per_km)} for v in vehicles],'routes':[{'id':r.id,'routeNo':r.route_no,'date':_dt(r.route_date),'vehicle':r.vehicle.vehicle_no,'warehouse':r.warehouse.name,'status':r.status,'km':_money(r.estimated_km),'cost':_money(r.estimated_cost),'score':_money(r.optimization_score),'stops':[{'sequence':s.sequence,'order':s.order.order_no,'customer':s.order.customer.name,'area':s.area,'km':_money(s.estimated_km_from_previous)} for s in r.stops.all()]} for r in routes]})
    data=_body(request);action=data.get('action','optimize')
    if action=='vehicle':
        v=m.FleetVehicle.objects.create(company=company,vehicle_no=data.get('vehicleNo') or f"DL-DEMO-{timezone.now().strftime('%H%M%S')}",vehicle_type=data.get('type','LCV'),capacity_kg=data.get('capacityKg',1200),driver_name=data.get('driver',''),driver_phone=data.get('phone',''),cost_per_km=data.get('costPerKm',18));return JsonResponse({'id':v.id},status=201)
    vehicle=m.FleetVehicle.objects.filter(company=company,is_active=True,pk=data.get('vehicleId')).first() or m.FleetVehicle.objects.filter(company=company,is_active=True).first(); warehouse=m.Warehouse.objects.filter(company=company,is_active=True,pk=data.get('warehouseId')).first() or m.Warehouse.objects.filter(company=company,is_active=True).first()
    if not vehicle or not warehouse:return JsonResponse({'detail':'Vehicle and warehouse are required.'},status=400)
    orders=list(m.Order.objects.filter(company=company).exclude(status__in=['Dispatched','Cancelled']).select_related('customer').order_by('customer__city','-total')[:25])
    route=m.RoutePlan.objects.create(company=company,route_no=f"ROUTE-{timezone.now().strftime('%y%m%d%H%M%S%f')}",vehicle=vehicle,warehouse=warehouse,route_date=data.get('date') or timezone.localdate(),estimated_km=max(12,len(orders)*Decimal('3.4')),optimization_score=91,created_by=request.api_user)
    for i,o in enumerate(orders,1):m.RoutePlanStop.objects.create(route=route,order=o,sequence=i,area=o.customer.city or 'Delhi NCR',delivery_window='10:00–18:00',estimated_km_from_previous=Decimal('3.4'),estimated_minutes=18,priority=1 if o.payment_status=='Paid' else 3)
    route.estimated_cost=(route.estimated_km*vehicle.cost_per_km).quantize(Decimal('0.01'));route.save(update_fields=['estimated_cost']);audit(request,'CREATE','RoutePlan',route.id,route.route_no);return JsonResponse({'id':route.id,'routeNo':route.route_no,'stops':len(orders),'km':_money(route.estimated_km),'cost':_money(route.estimated_cost)},status=201)


def _credit_score(customer):
    limit=Decimal(customer.credit_limit or 0); outstanding=Decimal(customer.outstanding or 0); utilisation=(outstanding/limit*100) if limit>0 else Decimal('100') if outstanding>0 else Decimal('0')
    overdue=m.LedgerEntry.objects.filter(customer=customer,due_date__lt=timezone.localdate(),entry_type='Invoice').aggregate(v=Sum('amount'))['v'] or Decimal('0')
    late_penalty=min(35,int((overdue/(limit or Decimal('1')))*35)); util_penalty=max(0,int((utilisation-60)/4)); score=max(10,min(100,92-late_penalty-util_penalty)); risk='Low' if score>=75 else 'Medium' if score>=55 else 'High'; suggested=(limit*Decimal('1.15') if score>=80 else limit if score>=55 else limit*Decimal('0.75')).quantize(Decimal('0.01'))
    return score,risk,utilisation,overdue,suggested

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def credit_risk(request):
    denied=_guard(request,['OWNER','MANAGER','ACCOUNTANT'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        scores=m.CustomerCreditScore.objects.filter(company=company).select_related('customer').order_by('-score'); apps=m.FinanceApplication.objects.filter(company=company).select_related('customer').order_by('-id')
        return JsonResponse({'summary':{'scored':scores.count(),'highRisk':scores.filter(risk_band='High').count(),'suggestedCredit':_money(scores.aggregate(v=Sum('suggested_limit'))['v'] or 0),'financePipeline':_money(apps.exclude(status__in=['Declined','Funded']).aggregate(v=Sum('requested_amount'))['v'] or 0)},'scores':[{'id':x.id,'customerId':x.customer_id,'customer':x.customer.name,'score':x.score,'risk':x.risk_band,'outstanding':_money(x.customer.outstanding),'creditLimit':_money(x.customer.credit_limit),'utilisation':_money(x.utilisation_percent),'overdue90':_money(x.overdue_90),'suggestedLimit':_money(x.suggested_limit),'factors':x.factors} for x in scores],'applications':[{'id':x.id,'applicationNo':x.application_no,'customer':x.customer.name if x.customer else 'Portfolio','type':x.finance_type,'amount':_money(x.requested_amount),'provider':x.provider,'status':x.status} for x in apps]})
    data=_body(request);action=data.get('action','rescore')
    if action=='finance':
        customer=m.Customer.objects.filter(company=company,pk=data.get('customerId')).first(); row=m.FinanceApplication.objects.create(company=company,customer=customer,application_no=f"FIN-{timezone.now().strftime('%y%m%d%H%M%S%f')}",finance_type=data.get('type','Receivable Finance'),requested_amount=data.get('amount',0),status='Ready',provider=data.get('provider','Provider pending'),payload=data.get('payload',{}),created_by=request.api_user);audit(request,'CREATE','FinanceApplication',row.id,row.application_no);return JsonResponse({'id':row.id,'applicationNo':row.application_no,'status':row.status},status=201)
    customers=m.Customer.objects.filter(company=company,is_active=True);count=0
    for c in customers:
        score,risk,util,overdue,suggested=_credit_score(c);m.CustomerCreditScore.objects.update_or_create(company=company,customer=c,defaults={'score':score,'risk_band':risk,'utilisation_percent':util,'overdue_90':overdue,'suggested_limit':suggested,'factors':{'paymentHistory':'derived from ledger','creditUtilisation':float(util),'overdueAmount':float(overdue)}});count+=1
    return JsonResponse({'scored':count})

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def security_center(request):
    denied=_guard(request,['OWNER'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        events=m.SecurityEvent.objects.filter(company=company).select_related('user').order_by('-created_at'); devices=m.TrustedDevice.objects.filter(company=company).select_related('user').order_by('-last_seen_at'); privacy=m.PrivacyRequest.objects.filter(company=company).order_by('-created_at')
        enabled=m.UserMFASetting.objects.filter(company=company,is_enabled=True).count(); users=m.Profile.objects.filter(company=company).count()
        return JsonResponse({'summary':{'mfaEnabled':enabled,'users':users,'trustedDevices':devices.filter(trusted=True).count(),'openPrivacyRequests':privacy.exclude(status__in=['Complete','Rejected']).count(),'criticalEvents':events.filter(severity='Critical').count()},'devices':[{'id':d.id,'user':d.user.get_full_name() or d.user.username,'name':d.device_name or d.device_id,'trusted':d.trusted,'ip':d.last_ip,'lastSeen':_dt(d.last_seen_at)} for d in devices],'events':[{'id':e.id,'type':e.event_type,'severity':e.severity,'user':e.user.get_full_name() if e.user else 'System','ip':e.ip_address,'createdAt':_dt(e.created_at)} for e in events],'privacy':[{'id':p.id,'requestNo':p.request_no,'subject':p.subject_name,'type':p.request_type,'status':p.status,'due':_dt(p.due_date)} for p in privacy]})
    data=_body(request);action=data.get('action')
    if action=='enable-mfa':
        raw=secrets.token_urlsafe(20); row,_=m.UserMFASetting.objects.update_or_create(user=request.api_user,defaults={'company':company,'method':'TOTP','secret_hash':hashlib.sha256(raw.encode()).hexdigest(),'is_enabled':True,'enabled_at':timezone.now()});m.SecurityEvent.objects.create(company=company,user=request.api_user,event_type='MFA_ENABLED',severity='Info');audit(request,'UPDATE','Security',request.api_user.id,'Enabled MFA');return JsonResponse({'enabled':True,'setupCode':raw,'note':'Show this once, then store it in an authenticator. Production should use a standards-compliant TOTP library.'})
    if action=='trust-device':
        did=data.get('deviceId') or secrets.token_hex(8); row,_=m.TrustedDevice.objects.update_or_create(company=company,user=request.api_user,device_id=did,defaults={'device_name':data.get('deviceName','Current browser'),'fingerprint_hash':hashlib.sha256(str(data.get('fingerprint',did)).encode()).hexdigest(),'last_ip':request.META.get('REMOTE_ADDR') or None,'trusted':True});m.SecurityEvent.objects.create(company=company,user=request.api_user,event_type='DEVICE_TRUSTED',severity='Info',device_id=did);return JsonResponse({'id':row.id,'trusted':True})
    if action=='privacy-request':
        row=m.PrivacyRequest.objects.create(company=company,request_no=f"PRIV-{timezone.now().strftime('%y%m%d%H%M%S%f')}",subject_name=data.get('name','Data subject'),subject_email=data.get('email',''),request_type=data.get('type','Access'),due_date=data.get('dueDate') or (timezone.localdate()+timedelta(days=30)),note=data.get('note',''));audit(request,'CREATE','PrivacyRequest',row.id,row.request_no);return JsonResponse({'id':row.id,'requestNo':row.request_no},status=201)
    if action=='consent':
        row=m.ConsentRecord.objects.create(company=company,subject_key=data.get('subjectKey','anonymous'),purpose=data.get('purpose','Customer communications'),granted=bool(data.get('granted',True)),source=data.get('source','Portal'));return JsonResponse({'id':row.id},status=201)
    return JsonResponse({'detail':'Unsupported action.'},status=400)

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def integration_hub(request):
    denied=_guard(request,['OWNER'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        connectors=m.IntegrationConnector.objects.filter(company=company).order_by('provider'); keys=m.DeveloperApiKey.objects.filter(company=company,revoked_at__isnull=True).order_by('-created_at'); hooks=m.WebhookSubscription.objects.filter(company=company).order_by('-created_at'); deliveries=m.IntegrationDelivery.objects.filter(company=company).order_by('-id')
        return JsonResponse({'summary':{'connected':connectors.filter(status='Connected').count(),'connectors':connectors.count(),'apiKeys':keys.count(),'webhooks':hooks.filter(is_active=True).count(),'failedDeliveries':deliveries.filter(status='Failed').count()},'connectors':[{'id':x.id,'provider':x.provider,'name':x.name,'status':x.status,'lastSync':_dt(x.last_sync_at),'lastError':x.last_error} for x in connectors],'apiKeys':[{'id':x.id,'name':x.name,'prefix':x.key_prefix,'scopes':x.scopes,'lastUsed':_dt(x.last_used_at),'createdAt':_dt(x.created_at)} for x in keys],'webhooks':[{'id':x.id,'event':x.event,'url':x.target_url,'active':x.is_active} for x in hooks],'deliveries':[{'id':x.id,'event':x.event,'status':x.status,'attempts':x.attempt_count,'error':x.last_error,'createdAt':_dt(x.created_at)} for x in deliveries]})
    data=_body(request);action=data.get('action')
    if action=='connector':
        row,_=m.IntegrationConnector.objects.update_or_create(company=company,provider=data.get('provider','CUSTOM'),name=data.get('name','Custom integration'),defaults={'status':data.get('status','Connected'),'config':data.get('config',{}),'last_sync_at':timezone.now() if data.get('status','Connected')=='Connected' else None});audit(request,'UPSERT','IntegrationConnector',row.id,row.name);return JsonResponse({'id':row.id,'status':row.status},status=201)
    if action=='api-key':
        raw='ssk_'+secrets.token_urlsafe(30);digest=hashlib.sha256(raw.encode()).hexdigest();row=m.DeveloperApiKey.objects.create(company=company,name=data.get('name','API client'),key_prefix=raw[:12],key_hash=digest,scopes=data.get('scopes',['orders:write']),created_by=request.api_user);audit(request,'CREATE','DeveloperApiKey',row.id,row.name);return JsonResponse({'id':row.id,'apiKey':raw,'prefix':row.key_prefix,'note':'This key is returned once. Store it securely.'},status=201)
    if action=='webhook':
        raw=secrets.token_urlsafe(24);row=m.WebhookSubscription.objects.create(company=company,event=data.get('event','order.created'),target_url=data.get('url','https://example.com/webhook'),signing_secret_hash=hashlib.sha256(raw.encode()).hexdigest());return JsonResponse({'id':row.id,'signingSecret':raw,'note':'Returned once; use it to verify deliveries when a worker/provider is connected.'},status=201)
    return JsonResponse({'detail':'Unsupported action.'},status=400)

@csrf_exempt
@require_http_methods(['POST'])
def public_order_api(request):
    raw=request.headers.get('X-SetuStock-Key',''); digest=hashlib.sha256(raw.encode()).hexdigest() if raw else ''
    key=m.DeveloperApiKey.objects.select_related('company').filter(key_hash=digest,revoked_at__isnull=True).first()
    if not key or 'orders:write' not in key.scopes:return JsonResponse({'detail':'Valid API key with orders:write scope required.'},status=401)
    data=_body(request); key.last_used_at=timezone.now();key.save(update_fields=['last_used_at'])
    channel,_=m.ExternalChannel.objects.get_or_create(company=key.company,name='Developer API',defaults={'provider':'CUSTOM','external_store_id':'public-v1','is_active':True})
    ext_id=data.get('externalId') or f"API-{timezone.now().strftime('%y%m%d%H%M%S%f')}"; order,created=m.ExternalOrder.objects.get_or_create(channel=channel,external_id=ext_id,defaults={'company':key.company,'customer_name':data.get('customerName','API Customer'),'customer_phone':data.get('phone',''),'total':data.get('total',0),'status':'New','raw_payload':data})
    return JsonResponse({'id':order.id,'externalId':order.external_id,'created':created,'status':order.status},status=201 if created else 200)


def _rebuild_profitability(company, start, end):
    m.ProfitabilitySnapshot.objects.filter(company=company,period_from=start,period_to=end).delete()
    customer_rows={}
    items=m.OrderItem.objects.filter(order__company=company,order__order_date__range=[start,end]).select_related('order__customer','product')
    for item in items:
        c=item.order.customer; key=str(c.id); row=customer_rows.setdefault(key,{'name':c.name,'revenue':Decimal('0'),'cogs':Decimal('0'),'discounts':Decimal('0')})
        row['revenue']+=Decimal(item.taxable_amount or 0); row['cogs']+=Decimal(item.product.purchase_price or 0)*Decimal(item.quantity or 0)
    discounts={str(x['customer']):Decimal(x['v'] or 0) for x in m.Order.objects.filter(company=company,order_date__range=[start,end]).values('customer').annotate(v=Sum('discount'))}
    returns={str(x['customer']):Decimal(x['v'] or 0) for x in m.ReturnOrder.objects.filter(company=company,return_type='Sales Return',return_date__range=[start,end],customer__isnull=False).values('customer').annotate(v=Sum('total'))}
    for key,row in customer_rows.items():
        disc=discounts.get(key,Decimal('0')); ret=returns.get(key,Decimal('0')); gross=row['revenue']-row['cogs']; contribution=gross-disc-ret; margin=(contribution/row['revenue']*100) if row['revenue'] else Decimal('0')
        m.ProfitabilitySnapshot.objects.create(company=company,dimension='Customer',entity_key=key,entity_name=row['name'],period_from=start,period_to=end,revenue=row['revenue'],cogs=row['cogs'],gross_profit=gross,discounts=disc,returns=ret,delivery_cost=0,finance_cost=0,contribution_profit=contribution,margin_percent=margin)
    return len(customer_rows)

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def executive_bi(request):
    denied=_guard(request,['OWNER','MANAGER','ACCOUNTANT'])
    if denied:return denied
    company=request.company; today=timezone.localdate(); start=today.replace(day=1); end=today
    if request.method=='POST':
        data=_body(request);start=date.fromisoformat(data.get('from')) if data.get('from') else start;end=date.fromisoformat(data.get('to')) if data.get('to') else end;count=_rebuild_profitability(company,start,end);audit(request,'REBUILD','ProfitabilitySnapshot',f'{start}:{end}',f'Rebuilt {count} profitability rows');return JsonResponse({'rebuilt':count,'from':_dt(start),'to':_dt(end)})
    rows=m.ProfitabilitySnapshot.objects.filter(company=company,period_from=start,period_to=end).order_by('-contribution_profit')
    if not rows.exists(): _rebuild_profitability(company,start,end);rows=m.ProfitabilitySnapshot.objects.filter(company=company,period_from=start,period_to=end).order_by('-contribution_profit')
    revenue=rows.aggregate(v=Sum('revenue'))['v'] or 0; contribution=rows.aggregate(v=Sum('contribution_profit'))['v'] or 0
    return JsonResponse({'summary':{'revenue':_money(revenue),'contribution':_money(contribution),'margin':round(float(contribution/revenue*100),2) if revenue else 0,'entities':rows.count()},'rows':[{'id':x.id,'dimension':x.dimension,'entity':x.entity_name,'revenue':_money(x.revenue),'cogs':_money(x.cogs),'grossProfit':_money(x.gross_profit),'discounts':_money(x.discounts),'returns':_money(x.returns),'deliveryCost':_money(x.delivery_cost),'financeCost':_money(x.finance_cost),'contribution':_money(x.contribution_profit),'margin':_money(x.margin_percent)} for x in rows[:100]]})


def _copilot_proposal(company,user,prompt):
    q=(prompt or '').lower()
    if any(x in q for x in ['collect','overdue','payment reminder']):
        customers=list(m.Customer.objects.filter(company=company,outstanding__gt=0).order_by('-outstanding')[:20]);return m.CopilotActionProposal.objects.create(company=company,requested_by=user,action_type='CREATE_COLLECTION_TASKS',title='Create collection tasks for outstanding customers',rationale=f'{len(customers)} customers have an outstanding balance. Human approval is required before tasks are created.',payload={'customerIds':[x.id for x in customers]},risk_level='Medium')
    if any(x in q for x in ['purchase','reorder','stock out','stockout']):
        recs=list(m.ProcurementRecommendation.objects.filter(company=company,status='Open').values_list('id',flat=True)[:30]);return m.CopilotActionProposal.objects.create(company=company,requested_by=user,action_type='APPROVE_PROCUREMENT_RECOMMENDATIONS',title='Approve reviewed procurement recommendations',rationale=f'{len(recs)} open recommendations are available. Approval changes recommendation state but does not send a supplier PO.',payload={'recommendationIds':recs},risk_level='High')
    return m.CopilotActionProposal.objects.create(company=company,requested_by=user,action_type='REVIEW_ONLY',title='Review business question',rationale='No safe transactional action was inferred. The proposal remains review-only.',payload={'prompt':prompt},risk_level='Low')

def _execute_copilot(request, proposal):
    if proposal.action_type=='CREATE_COLLECTION_TASKS':
        created=0
        for c in m.Customer.objects.filter(company=request.company,id__in=proposal.payload.get('customerIds',[]),outstanding__gt=0):
            _,was=m.CollectionTask.objects.get_or_create(company=request.company,customer=c,due_date=timezone.localdate(),status='Open',defaults={'assigned_to':request.api_user,'amount_due':c.outstanding,'priority':'High' if c.outstanding>=50000 else 'Normal','notes':'Created by approved AI copilot proposal'});created+=int(was)
        return {'createdCollectionTasks':created}
    if proposal.action_type=='APPROVE_PROCUREMENT_RECOMMENDATIONS':
        count=m.ProcurementRecommendation.objects.filter(company=request.company,id__in=proposal.payload.get('recommendationIds',[]),status='Open').update(status='Approved');return {'approvedRecommendations':count,'purchaseOrdersSent':0}
    return {'executed':False,'note':'Review-only proposal; no transaction performed.'}

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def copilot_actions(request):
    denied=_guard(request,['OWNER','MANAGER','SALES','WAREHOUSE','ACCOUNTANT'])
    if denied:return denied
    company=request.company
    if request.method=='GET':
        rows=m.CopilotActionProposal.objects.filter(company=company).select_related('requested_by','approved_by').order_by('-id')
        return JsonResponse({'summary':{'proposed':rows.filter(status='Proposed').count(),'executed':rows.filter(status='Executed').count(),'highRisk':rows.filter(risk_level='High',status='Proposed').count()},'proposals':[{'id':x.id,'title':x.title,'actionType':x.action_type,'rationale':x.rationale,'risk':x.risk_level,'status':x.status,'requestedBy':x.requested_by.get_full_name() if x.requested_by else 'System','approvedBy':x.approved_by.get_full_name() if x.approved_by else '', 'result':x.result,'createdAt':_dt(x.created_at)} for x in rows]})
    data=_body(request);action=data.get('action','propose')
    if action=='propose':
        row=_copilot_proposal(company,request.api_user,data.get('prompt','Prepare collection tasks for overdue customers'));audit(request,'PROPOSE','CopilotActionProposal',row.id,row.title);return JsonResponse({'id':row.id,'title':row.title,'actionType':row.action_type,'risk':row.risk_level,'status':row.status,'rationale':row.rationale},status=201)
    row=m.CopilotActionProposal.objects.filter(company=company,pk=data.get('id')).first()
    if not row:return JsonResponse({'detail':'Proposal not found.'},status=404)
    if request.api_user.profile.role not in ['OWNER','MANAGER']:return JsonResponse({'detail':'Owner or manager approval is required.'},status=403)
    if action=='reject': row.status='Rejected';row.approved_by=request.api_user;row.approved_at=timezone.now();row.save(update_fields=['status','approved_by','approved_at']);audit(request,'REJECT','CopilotActionProposal',row.id,row.title);return JsonResponse({'id':row.id,'status':row.status})
    if action=='approve':
        if row.status!='Proposed':return JsonResponse({'detail':'Only proposed actions can be approved.'},status=400)
        with transaction.atomic():
            row.status='Approved';row.approved_by=request.api_user;row.approved_at=timezone.now();row.save(update_fields=['status','approved_by','approved_at']);
            try: result=_execute_copilot(request,row);row.status='Executed';row.result=result;row.executed_at=timezone.now();row.save(update_fields=['status','result','executed_at'])
            except Exception as exc: row.status='Failed';row.result={'error':str(exc)};row.save(update_fields=['status','result']);raise
        audit(request,'EXECUTE','CopilotActionProposal',row.id,row.title,changes=row.result);return JsonResponse({'id':row.id,'status':row.status,'result':row.result})
    return JsonResponse({'detail':'Unsupported action.'},status=400)
