import json, secrets, hashlib
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

@csrf_exempt
@require_http_methods(['GET','POST'])
@api_auth_required
def crm(request):
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
    company=request.company
    if request.method=='GET':
        schemes=m.ManufacturerScheme.objects.filter(company=company).select_related('supplier').order_by('-end_date')[:50]
        claims=m.SchemeClaim.objects.filter(company=company).select_related('scheme','scheme__supplier').order_by('-id')[:50]
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
    company=request.company
    if request.method=='GET':
        rows=m.GSTReconciliationItem.objects.filter(company=company).select_related('supplier').order_by('-invoice_date','-id')[:100]
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
    company=request.company
    if request.method=='GET':
        scores=m.VendorScorecard.objects.filter(company=company).select_related('supplier').order_by('-overall_score')[:50]
        recs=m.ProcurementRecommendation.objects.filter(company=company).select_related('product','supplier').order_by('status','product__name')[:100]
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
    company=request.company
    if request.method=='GET':
        vehicles=m.FleetVehicle.objects.filter(company=company,is_active=True).order_by('vehicle_no')
        routes=m.RoutePlan.objects.filter(company=company).select_related('vehicle','warehouse').prefetch_related('stops__order__customer').order_by('-route_date','-id')[:30]
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
