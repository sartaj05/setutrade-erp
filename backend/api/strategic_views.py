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
