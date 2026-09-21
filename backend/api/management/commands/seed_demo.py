from datetime import date
import hashlib
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import (
    ApprovalPolicy, Branch, Company, Customer, CustomerPortalAccess, DeliveryRun, DeliveryStop, Invoice, InventoryMovement, LedgerEntry, Notification,
    Order, OrderItem, Payment, PriceList, PriceRule, Product, Profile, PurchaseItem,
    PurchaseOrder, ReorderSuggestion, SalesTarget, SalesVisit, StockAdjustment,
    StockBalance, StockTransfer, StockTransferItem, Supplier, TaxNote, Warehouse,
    WhatsAppMessage, WhatsAppOrderDraft,
)

from api.models import (
    PaymentPromise, CollectionTask, PaymentTransaction, PaymentLink, CollectionReminder, ReceivableFinanceExport,
    WarehouseBin, BinStock, PickList, PickListItem, PickWave, PackingSlip, CycleCount, SupplierPortalAccess, SupplierPortalSubmission,
    AutomationRule, AutomationRun, ExternalChannel, ExternalOrder, ExternalOrderItem, DistributionNetwork, NetworkMember, NetworkSnapshot,
    CRMLead, CRMActivity, ManufacturerScheme, SchemeClaim, GSTReconciliationItem, VendorScorecard, ProcurementRecommendation,
    FleetVehicle, RoutePlan, RoutePlanStop, CustomerCreditScore, FinanceApplication, UserMFASetting, TrustedDevice, SecurityEvent, PrivacyRequest, ConsentRecord,
    IntegrationConnector, DeveloperApiKey, WebhookSubscription, IntegrationDelivery, ProfitabilitySnapshot, CopilotActionProposal,
    ProductMasterProfile, ProductChangeRequest, InventoryLot, SerialUnit, TraceabilityEvent, BankAccount, BankTransaction, CashFlowForecast,
    RateAgreement, RateAgreementItem, Tender, QualityInspection, QuarantineStock, SupplyPlanScenario, ReplenishmentPlan, ServiceTicket, RMA,
    ExpenseClaim, PettyCashAccount, PettyCashTransaction, ReportDefinition, ScheduledReport, ReportRun, ServiceHealth, BackgroundJob, WebhookReplay, AlertPolicy,
)

ACCOUNTS = [
    ('owner','Arjun','Khanna','owner@setustock.demo','OWNER'),
    ('manager','Meera','Sethi','manager@setustock.demo','MANAGER'),
    ('sales','Rohit','Bansal','sales@setustock.demo','SALES'),
    ('warehouse','Imran','Ali','warehouse@setustock.demo','WAREHOUSE'),
    ('accountant','Nisha','Gupta','accountant@setustock.demo','ACCOUNTANT'),
]

PRODUCTS = [
    ('PC-25-RD','Polycab 2.5mm Wire Red','Wires & Cables',7,'coil',1820,2040,12,'A-01','8901002500017','8544',18),
    ('HA-LED-12','Havells 12W LED Bulb','Lighting',86,'pcs',118,145,30,'B-07','8901762048129','8539',12),
    ('AN-MCB-32','Anchor 32A DP MCB','Switchgear',24,'pcs',412,495,20,'C-11','8901442032036','8536',18),
    ('GM-PLT-8','GM 8 Module Plate','Switches',12,'pcs',176,225,15,'D-04','8906084407084','8538',18),
    ('RR-4SQ-BK','RR Kabel 4 sq mm Black','Wires & Cables',18,'coil',2960,3290,10,'A-04','8901004000412','8544',18),
    ('LE-FAN-48','Legrand Exhaust Fan 48W','Fans',9,'pcs',1780,2140,8,'E-02','8905554801048','8414',18),
]

CUSTOMERS = [
    ('C-101','R.K. Trading Co.','Ghaziabad','Uttar Pradesh','9810012233','09AABCR1234A1Z5',58240,150000,date(2026,9,28)),
    ('C-102','Metro Electricals','Noida','Uttar Pradesh','9871123456','09AAACM9000B1Z3',38400,100000,date(2026,9,9)),
    ('C-103','Ahuja Enterprises','Delhi','Delhi','9899011122','07AAECA3344M1Z2',0,200000,None),
    ('C-104','NCR Buildmart','Gurugram','Haryana','9958012211','06AAGFN7788B1Z9',76750,250000,date(2026,9,25)),
    ('C-105','Sethi Hardware House','Faridabad','Haryana','9818817717','06AAXPS4455D1Z1',124600,180000,date(2026,9,18)),
]


class Command(BaseCommand):
    help = 'Create a tenant-aware SetuStock demo company, users and transactional data.'

    def handle(self, *args, **options):
        company, _ = Company.objects.update_or_create(slug='khanna-electrical', defaults={
            'name':'Khanna Electrical Distributors','gstin':'07AAAPK1234K1Z5','pan':'AAAPK1234K',
            'state':'Delhi','address':'Bhagirath Palace, Chandni Chowk, Delhi 110006','phone':'011-41234567',
            'email':'accounts@khanna.demo','bank_name':'Demo Bank','bank_account':'XXXX1206','ifsc':'DEMO0001206',
            'upi_id':'khanna@upi','invoice_prefix':'INV-2026',
        })
        branch, _ = Branch.objects.update_or_create(company=company, code='DEL', defaults={'name':'Delhi HQ','city':'Delhi','address':company.address,'gstin':company.gstin,'phone':company.phone})

        users = {}
        for username, first, last, email, role in ACCOUNTS:
            user, _ = User.objects.get_or_create(username=username)
            user.first_name, user.last_name, user.email, user.is_active = first, last, email, True
            user.set_password('demo123'); user.save()
            Profile.objects.update_or_create(user=user, defaults={'role':role,'business_name':company.name,'company':company,'branch':branch})
            users[role] = user

        warehouses = {}
        for code, name, city in [('WH-DEL','Delhi Central','Delhi'),('WH-NOI','Noida Hub','Noida'),('WH-GGN','Gurugram Depot','Gurugram')]:
            w, _ = Warehouse.objects.update_or_create(company=company, code=code, defaults={'branch':branch,'name':name,'city':city,'address':f'{city} distribution facility'})
            warehouses[code] = w

        products = {}
        for sku, name, category, stock, unit, buy, sell, reorder, location, barcode, hsn, gst in PRODUCTS:
            p, _ = Product.objects.update_or_create(company=company, sku=sku, defaults={'name':name,'category':category,'unit':unit,'purchase_price':buy,'sell_price':sell,'reorder_level':reorder,'location':location,'barcode':barcode,'hsn_code':hsn,'gst_rate':gst})
            products[sku] = p
        allocation = {'WH-DEL': Decimal('0.65'), 'WH-NOI': Decimal('0.22'), 'WH-GGN': Decimal('0.13')}
        for sku, _, _, stock, *_ in PRODUCTS:
            remaining = Decimal(str(stock))
            for idx, (code, ratio) in enumerate(allocation.items()):
                qty = remaining if idx == 2 else (Decimal(str(stock)) * ratio).quantize(Decimal('0.01'))
                remaining -= qty if idx < 2 else Decimal('0')
                StockBalance.objects.update_or_create(warehouse=warehouses[code], product=products[sku], defaults={'quantity':qty,'reserved':0})
            total = StockBalance.objects.filter(product=products[sku]).aggregate(v=__import__('django.db.models', fromlist=['Sum']).Sum('quantity'))['v'] or 0
            Product.objects.filter(pk=products[sku].pk).update(stock=total)

        customers = {}
        for code,name,city,state,phone,gstin,outstanding,limit,due in CUSTOMERS:
            c, _ = Customer.objects.update_or_create(company=company, code=code, defaults={'name':name,'city':city,'state':state,'phone':phone,'gstin':gstin,'outstanding':outstanding,'credit_limit':limit,'due_date':due,'address':f'{city}, {state}'})
            customers[code] = c

        CustomerPortalAccess.objects.update_or_create(
            company=company, customer=customers['C-101'],
            defaults={'email':'dealer@setustock.demo','pin_hash':make_password('1234'),'is_active':True},
        )
        ApprovalPolicy.objects.update_or_create(company=company,key='discount',defaults={'label':'Discount above 10%','threshold':10,'approver_role':'MANAGER','is_active':True})
        ApprovalPolicy.objects.update_or_create(company=company,key='credit',defaults={'label':'Credit override above ₹50,000','threshold':50000,'approver_role':'OWNER','is_active':True})

        suppliers = {}
        for code,name,city,outstanding in [('S-001','Polycab India Supply','Delhi',212600),('S-002','Havells Channel Partner','Noida',124850),('S-003','Legrand NCR Distribution','Gurugram',0)]:
            s,_=Supplier.objects.update_or_create(company=company,code=code,defaults={'name':name,'city':city,'state':'Delhi NCR','phone':'9810000001','gstin':'07AAACP0001A1Z1','outstanding':outstanding})
            suppliers[code]=s

        order_specs = [
            ('SO-1097','C-101','AN-MCB-32',20,495,'Ready','Credit',date(2026,9,21)),
            ('SO-1096','C-102','HA-LED-12',40,145,'Processing','Overdue',date(2026,9,21)),
            ('SO-1095','C-103','RR-4SQ-BK',20,3290,'Packed','Paid',date(2026,9,20)),
            ('SO-1094','C-104','GM-PLT-8',120,225,'Dispatched','Credit',date(2026,9,20)),
        ]
        orders = {}
        for no,ccode,sku,qty,price,status,payment,odate in order_specs:
            p=products[sku]; taxable=Decimal(str(qty))*Decimal(str(price)); tax=(taxable*Decimal(str(p.gst_rate))/100).quantize(Decimal('0.01')); total=taxable+tax
            order,_=Order.objects.update_or_create(order_no=no,defaults={'company':company,'branch':branch,'warehouse':warehouses['WH-DEL'],'customer':customers[ccode],'subtotal':taxable,'tax':tax,'total':total,'status':status,'payment_status':payment,'order_date':odate,'created_by':users['SALES']})
            OrderItem.objects.update_or_create(order=order,product=p,defaults={'quantity':qty,'unit_price':price,'gst_rate':p.gst_rate,'taxable_amount':taxable,'tax_amount':tax,'line_total':total})
            orders[no]=order

        run, _ = DeliveryRun.objects.update_or_create(
            run_no='RUN-260921-07',
            defaults={'company':company,'route_name':'Noida Central','driver_name':'Vikas Kumar','driver_phone':'9810007788','vehicle_no':'DL1L AB 4421','delivery_date':date(2026,9,21),'status':'Out for Delivery','created_by':users['MANAGER']},
        )
        for seq, order_no in enumerate(['SO-1097','SO-1096'], 1):
            DeliveryStop.objects.update_or_create(run=run, order=orders[order_no], defaults={'sequence':seq,'cod_amount':orders[order_no].total if orders[order_no].payment_status != 'Paid' else 0})

        invoice_specs = [
            ('INV-2026-1184','SO-1097','09AABCR1234A1Z5','Unpaid',date(2026,9,21)),
            ('INV-2026-1183','SO-1095','07AAECA3344M1Z2','Paid',date(2026,9,20)),
            ('INV-2026-1182','SO-1094','06AAGFN7788B1Z9','Credit',date(2026,9,20)),
        ]
        invoices={}
        for inv_no,order_no,gstin,status,inv_date in invoice_specs:
            order=orders[order_no]; tax=order.tax; cgst=(tax/2).quantize(Decimal('0.01')); sgst=tax-cgst
            inv,_=Invoice.objects.update_or_create(invoice_no=inv_no,defaults={'company':company,'order':order,'gstin':gstin,'taxable_amount':order.subtotal,'cgst':cgst,'sgst':sgst,'igst':0,'total':order.total,'status':status,'invoice_date':inv_date,'due_date':inv_date.replace(day=min(28,inv_date.day+7)),'place_of_supply':order.customer.state,'supply_type':'Intra-state','terms':'Payment as per agreed credit terms.'})
            invoices[inv_no]=inv

        po,_=PurchaseOrder.objects.update_or_create(po_no='PO-2026-084',defaults={'company':company,'branch':branch,'warehouse':warehouses['WH-DEL'],'supplier':suppliers['S-001'],'status':'Partial','order_date':date(2026,9,20),'expected_date':date(2026,9,23),'total':186400,'created_by':users['MANAGER']})
        PurchaseItem.objects.update_or_create(purchase=po,product=products['PC-25-RD'],defaults={'quantity':100,'received_quantity':60,'unit_price':1820})

        for code,reference,amount,entry_date,due in [('C-105','INV-2026-1164',124600,date(2026,8,18),date(2026,9,18)),('C-102','INV-2026-1171',38400,date(2026,8,9),date(2026,9,9)),('C-101','INV-2026-1184',58240,date(2026,9,21),date(2026,9,28))]:
            LedgerEntry.objects.update_or_create(company=company,customer=customers[code],reference=reference,defaults={'entry_type':'Invoice','amount':amount,'entry_date':entry_date,'due_date':due,'note':'Demo receivable'})

        price_list,_=PriceList.objects.update_or_create(company=company,name='Electrical Dealer Standard',defaults={'valid_from':date(2026,9,1),'valid_to':date(2026,12,31)})
        PriceRule.objects.update_or_create(price_list=price_list,product=products['AN-MCB-32'],min_quantity=10,defaults={'price':465,'discount_percent':6,'scheme_text':'10+ dealer slab'})

        transfer,_=StockTransfer.objects.update_or_create(transfer_no='TR-2026-031',defaults={'company':company,'from_warehouse':warehouses['WH-DEL'],'to_warehouse':warehouses['WH-NOI'],'transfer_date':date(2026,9,21),'status':'In Transit','created_by':users['WAREHOUSE']})
        StockTransferItem.objects.update_or_create(transfer=transfer,product=products['HA-LED-12'],defaults={'quantity':50})

        draft,_=WhatsAppOrderDraft.objects.update_or_create(draft_no='WA-260921-014',defaults={'company':company,'customer':customers['C-101'],'raw_message':'Need 20 Anchor 32A MCB and 10 Havells 12W LED bulbs','parsed_items':[{'productId':products['AN-MCB-32'].id,'sku':'AN-MCB-32','name':'Anchor 32A DP MCB','quantity':20,'unit':'pcs','price':495,'available':24},{'productId':products['HA-LED-12'].id,'sku':'HA-LED-12','name':'Havells 12W LED Bulb','quantity':10,'unit':'pcs','price':145,'available':86}],'estimated_total':11350})
        WhatsAppMessage.objects.update_or_create(company=company,customer=customers['C-101'],message=draft.raw_message,defaults={'direction':'Inbound','status':'Received'})

        TaxNote.objects.update_or_create(note_no='CN-2026-043',defaults={'company':company,'note_type':'Credit Note','customer':customers['C-102'],'invoice':None,'taxable_amount':4000,'gst_amount':720,'total':4720,'note_date':date(2026,9,19),'reason':'2 damaged MCBs returned'})
        SalesVisit.objects.update_or_create(company=company,salesperson=users['SALES'],customer=customers['C-101'],visit_date=date(2026,9,21),defaults={'status':'Visited','territory':'Ghaziabad East','order_value':58240,'collection_amount':18000,'notes':'Order confirmed; next visit Friday.'})
        SalesTarget.objects.update_or_create(company=company,salesperson=users['SALES'],month=date(2026,9,1),defaults={'target_sales':1200000,'target_collection':600000})
        for sku,risk,daily,lead,suggested in [('PC-25-RD','High',3.2,5,50),('GM-PLT-8','High',2.1,7,36),('AN-MCB-32','Low',2.4,4,20)]:
            p=products[sku]; balance=StockBalance.objects.filter(product=p,warehouse=warehouses['WH-DEL']).first(); stock=balance.quantity if balance else p.stock; days=(stock/Decimal(str(daily))).quantize(Decimal('0.01')) if daily else 99
            ReorderSuggestion.objects.update_or_create(product=p,warehouse=warehouses['WH-DEL'],defaults={'current_stock':stock,'avg_daily_sales':daily,'lead_time_days':lead,'suggested_quantity':suggested,'days_cover':days,'risk':risk})
        Notification.objects.get_or_create(company=company,user=None,title='Low stock needs attention',message='Polycab 2.5mm Wire Red is below its reorder level.',level='warning',module='insights',entity_id=str(products['PC-25-RD'].id))
        Notification.objects.get_or_create(company=company,user=None,title='Collections follow-up',message='Two customer balances are overdue.',level='critical',module='ledger')


        # Growth v3 demo data: collections, WMS, supplier collaboration, automations and channels.
        PaymentPromise.objects.update_or_create(company=company, customer=customers['C-105'], promised_date=date(2026,9,25), defaults={'promised_amount':50000,'status':'Open','notes':'Customer committed partial payment','created_by':users['SALES']})
        CollectionTask.objects.update_or_create(company=company, customer=customers['C-105'], due_date=date(2026,9,21), defaults={'assigned_to':users['SALES'],'amount_due':124600,'priority':'High','status':'Open','notes':'Call before noon'})
        tx,_=PaymentTransaction.objects.update_or_create(company=company, reference='UPI-DEMO-24000', defaults={'customer':customers['C-103'],'method':'UPI','amount':24000,'transaction_date':date(2026,9,21),'status':'Matched','created_by':users['ACCOUNTANT']})
        PaymentLink.objects.update_or_create(token='demo-rk-payment-link', defaults={'company':company,'customer':customers['C-101'],'invoice':invoices['INV-2026-1184'],'amount':invoices['INV-2026-1184'].total,'status':'Active'})
        CollectionReminder.objects.update_or_create(company=company, customer=customers['C-101'], invoice=invoices['INV-2026-1184'], message='Friendly reminder: INV-2026-1184 is due soon.', defaults={'channel':'WhatsApp','scheduled_for':__import__('django.utils.timezone',fromlist=['now']).now(),'status':'Scheduled'})

        bin_a,_=WarehouseBin.objects.update_or_create(warehouse=warehouses['WH-DEL'],code='A-01-01',defaults={'zone':'Fast Moving','capacity':120})
        bin_b,_=WarehouseBin.objects.update_or_create(warehouse=warehouses['WH-DEL'],code='C-04-03',defaults={'zone':'Switchgear','capacity':80})
        BinStock.objects.update_or_create(bin=bin_a,product=products['PC-25-RD'],defaults={'quantity':7})
        BinStock.objects.update_or_create(bin=bin_b,product=products['AN-MCB-32'],defaults={'quantity':24})
        pick,_=PickList.objects.update_or_create(pick_no='PICK-260921-019',defaults={'company':company,'warehouse':warehouses['WH-DEL'],'status':'Picking','assigned_to':users['WAREHOUSE']})
        PickListItem.objects.update_or_create(pick_list=pick,order=orders['SO-1097'],product=products['AN-MCB-32'],defaults={'source_bin':bin_b,'requested_qty':20,'picked_qty':12})
        CycleCount.objects.update_or_create(company=company,warehouse=warehouses['WH-DEL'],bin=bin_a,product=products['PC-25-RD'],defaults={'expected_qty':7,'counted_qty':6,'status':'Counted','counted_by':users['WAREHOUSE']})
        wave,_=PickWave.objects.update_or_create(wave_no='WAVE-260921-03',defaults={'company':company,'warehouse':warehouses['WH-DEL'],'status':'Released','created_by':users['WAREHOUSE']})
        wave.pick_lists.add(pick)
        PackingSlip.objects.update_or_create(package_no='PKG-260921-18',defaults={'company':company,'warehouse':warehouses['WH-DEL'],'order':orders['SO-1095'],'pick_list':None,'carton_count':2,'weight_kg':Decimal('12.50'),'status':'Packed','packed_by':users['WAREHOUSE']})

        SupplierPortalAccess.objects.update_or_create(company=company,supplier=suppliers['S-001'],defaults={'email':'supplier@setustock.demo','pin_hash':make_password('1234'),'is_active':True})
        SupplierPortalSubmission.objects.get_or_create(company=company,supplier=suppliers['S-001'],purchase_order=po,submission_type='ETA',defaults={'payload':{'eta':'2026-09-23','note':'Truck dispatched from Bhiwadi.'},'status':'Submitted'})

        AutomationRule.objects.update_or_create(company=company,name='Overdue > ₹50k collection escalation',defaults={'event':'invoice.overdue','conditions':{'outstanding':{'gte':50000}},'actions':[{'type':'create_collection_task'},{'type':'notify','title':'High-value overdue customer','module':'collections'}],'is_active':True,'created_by':users['OWNER']})
        AutomationRule.objects.update_or_create(company=company,name='Low stock buyer alert',defaults={'event':'stock.low','conditions':{'daysCover':{'gt':0}},'actions':[{'type':'notify','title':'Reorder review required','module':'insights'}],'is_active':True,'created_by':users['OWNER']})

        web_channel,_=ExternalChannel.objects.update_or_create(company=company,name='Khanna Web Catalogue',defaults={'provider':'WEBSITE','external_store_id':'web-delhi-01','is_active':True})
        ext_order,_=ExternalOrder.objects.update_or_create(channel=web_channel,external_id='WEB-44182',defaults={'company':company,'customer_name':'Bright Electricals','customer_phone':'9811004411','total':26480,'status':'New','raw_payload':{'source':'demo'}})
        ExternalOrderItem.objects.update_or_create(external_order=ext_order,external_sku='AN-MCB-32',defaults={'product':products['AN-MCB-32'],'name':products['AN-MCB-32'].name,'quantity':20,'unit_price':495})
        ExternalChannel.objects.update_or_create(company=company,name='ONDC Seller Adapter',defaults={'provider':'ONDC','external_store_id':'pending-credentials','is_active':False})

        demo_partner,_=Company.objects.update_or_create(slug='noida-channel-demo',defaults={'name':'Noida Channel Demo','state':'Uttar Pradesh','is_active':True})
        network,_=DistributionNetwork.objects.update_or_create(code='NCR-ELEC',defaults={'owner_company':company,'name':'North India Electrical Network','is_active':True})
        owner_member,_=NetworkMember.objects.update_or_create(network=network,company=company,defaults={'region':'Delhi','territory':'Central Delhi','share_inventory':True,'share_secondary_sales':True})
        partner_member,_=NetworkMember.objects.update_or_create(network=network,company=demo_partner,defaults={'region':'Uttar Pradesh','territory':'Noida','share_inventory':True,'share_secondary_sales':True})
        NetworkSnapshot.objects.update_or_create(network=network,member=owner_member,snapshot_date=date(2026,9,21),defaults={'inventory_value':3184500,'stock_units':156,'secondary_sales':4286400,'open_orders':34,'product_summary':[]})
        NetworkSnapshot.objects.update_or_create(network=network,member=partner_member,snapshot_date=date(2026,9,21),defaults={'inventory_value':1684200,'stock_units':98,'secondary_sales':2248000,'open_orders':17,'product_summary':[]})

        # Growth v4 demo data: CRM, schemes, GST reconciliation, procurement, fleet, credit, security, integrations, BI and copilot.
        lead,_=CRMLead.objects.update_or_create(company=company,lead_no='LEAD-2609-041',defaults={'name':'Sanjay Verma','business_name':'Verma Electrical House','phone':'9810099001','source':'Referral','territory':'West Delhi','status':'Negotiation','estimated_value':185000,'expected_close':date(2026,9,28),'owner':users['SALES']})
        CRMActivity.objects.get_or_create(company=company,lead=lead,activity_type='Meeting',note='Commercial terms reviewed; revised quotation requested.',defaults={'next_follow_up':timezone.now()+__import__('datetime').timedelta(days=2),'created_by':users['SALES']})
        lead2,_=CRMLead.objects.update_or_create(company=company,lead_no='LEAD-2609-042',defaults={'name':'Pooja Jain','business_name':'Jain Buildmart','phone':'9810099002','source':'Website','territory':'Noida','status':'Quoted','estimated_value':242000,'expected_close':date(2026,10,3),'owner':users['SALES']})

        scheme,_=ManufacturerScheme.objects.update_or_create(company=company,supplier=suppliers['S-001'],name='Q3 Electrical Growth Rebate',defaults={'scheme_type':'Rebate','start_date':date(2026,7,1),'end_date':date(2026,9,30),'target_value':5000000,'rebate_percent':Decimal('1.50'),'rules':{'basis':'purchase_value'}})
        SchemeClaim.objects.update_or_create(company=company,scheme=scheme,claim_no='CLM-2609-014',defaults={'period_from':date(2026,7,1),'period_to':date(2026,9,30),'eligible_value':4280000,'claim_amount':64200,'status':'Accrued','evidence':['purchase-register:q3']})

        GSTReconciliationItem.objects.update_or_create(company=company,invoice_no='SUP-8847',source='IMS',defaults={'supplier':suppliers['S-001'],'invoice_date':date(2026,9,20),'gstin':'07AAACP0001A1Z1','books_taxable':134444,'books_tax':24200,'portal_taxable':121111,'portal_tax':21800,'difference':2400,'status':'Mismatch'})
        GSTReconciliationItem.objects.update_or_create(company=company,invoice_no='SUP-8744',source='IMS',defaults={'supplier':suppliers['S-002'],'invoice_date':date(2026,9,18),'gstin':'07AAACP0001A1Z1','books_taxable':102444,'books_tax':18440,'portal_taxable':102444,'portal_tax':18440,'difference':0,'status':'Matched'})

        score,_=VendorScorecard.objects.update_or_create(company=company,supplier=suppliers['S-001'],defaults={'price_score':90,'fill_rate':96,'on_time_rate':95,'quality_score':98,'payment_term_score':84,'overall_score':94,'avg_lead_days':4})
        VendorScorecard.objects.update_or_create(company=company,supplier=suppliers['S-002'],defaults={'price_score':88,'fill_rate':91,'on_time_rate':86,'quality_score':97,'payment_term_score':82,'overall_score':88,'avg_lead_days':6})
        ProcurementRecommendation.objects.update_or_create(company=company,product=products['PC-25-RD'],supplier=suppliers['S-001'],defaults={'recommended_qty':50,'expected_unit_cost':1820,'expected_lead_days':4,'reason':'Low days cover; supplier has strong reliability score.','status':'Open'})

        vehicle,_=FleetVehicle.objects.update_or_create(company=company,vehicle_no='DL1LAB4421',defaults={'vehicle_type':'LCV','capacity_kg':1400,'driver_name':'Vikas Kumar','driver_phone':'9810007788','cost_per_km':18,'is_active':True})
        route,_=RoutePlan.objects.update_or_create(route_no='ROUTE-260921-07',defaults={'company':company,'vehicle':vehicle,'warehouse':warehouses['WH-DEL'],'route_date':date(2026,9,21),'status':'Released','estimated_km':68,'estimated_cost':1224,'optimization_score':93,'created_by':users['MANAGER']})
        for seq,no,km in [(1,'SO-1097',16),(2,'SO-1096',14)]: RoutePlanStop.objects.update_or_create(route=route,order=orders[no],defaults={'sequence':seq,'area':orders[no].customer.city,'delivery_window':'10:00-18:00','estimated_km_from_previous':km,'estimated_minutes':35,'priority':2})

        CustomerCreditScore.objects.update_or_create(company=company,customer=customers['C-101'],defaults={'score':82,'risk_band':'Low','avg_payment_delay_days':4,'overdue_90':0,'utilisation_percent':Decimal('38.83'),'suggested_limit':172500,'factors':{'paymentHistory':'stable','creditUtilisation':38.83}})
        CustomerCreditScore.objects.update_or_create(company=company,customer=customers['C-105'],defaults={'score':43,'risk_band':'High','avg_payment_delay_days':26,'overdue_90':78000,'utilisation_percent':Decimal('69.22'),'suggested_limit':135000,'factors':{'paymentHistory':'late','overdueAmount':78000}})
        FinanceApplication.objects.update_or_create(company=company,application_no='FIN-260921-03',defaults={'customer':customers['C-105'],'finance_type':'Receivable Finance','requested_amount':220000,'status':'Ready','provider':'TReDS-ready export','payload':{'note':'Provider onboarding required'},'created_by':users['ACCOUNTANT']})

        UserMFASetting.objects.update_or_create(user=users['OWNER'],defaults={'company':company,'method':'TOTP','secret_hash':hashlib.sha256(b'demo-not-a-real-secret').hexdigest(),'is_enabled':True,'enabled_at':timezone.now()})
        TrustedDevice.objects.update_or_create(company=company,user=users['OWNER'],device_id='office-chrome-demo',defaults={'device_name':'Chrome - Windows Office','fingerprint_hash':hashlib.sha256(b'office-chrome-demo').hexdigest(),'last_ip':'10.0.0.24','trusted':True})
        SecurityEvent.objects.get_or_create(company=company,user=None,event_type='FAILED_LOGIN_BURST',severity='Critical',defaults={'ip_address':'203.0.113.44','detail':{'attempts':7,'windowMinutes':10}})
        PrivacyRequest.objects.update_or_create(company=company,request_no='PRIV-2609-004',defaults={'subject_name':'Demo customer contact','subject_email':'privacy@example.com','request_type':'Export','status':'Processing','due_date':date(2026,10,10),'note':'Demo data export workflow'})
        ConsentRecord.objects.get_or_create(company=company,subject_key='dealer@setustock.demo',purpose='Order and payment notifications',defaults={'granted':True,'source':'Dealer Portal'})

        IntegrationConnector.objects.update_or_create(company=company,provider='WHATSAPP',name='Meta Business Messaging',defaults={'status':'Connected','config':{'credentialMode':'environment'},'last_sync_at':timezone.now()})
        IntegrationConnector.objects.update_or_create(company=company,provider='TALLY',name='Finance Export Bridge',defaults={'status':'Connected','config':{'mode':'file-export'},'last_sync_at':timezone.now()})
        raw_demo_key='ssk_demo_public_order_key'; DeveloperApiKey.objects.update_or_create(key_hash=hashlib.sha256(raw_demo_key.encode()).hexdigest(),defaults={'company':company,'name':'Demo website','key_prefix':raw_demo_key[:12],'scopes':['orders:write'],'created_by':users['OWNER']})
        hook,_=WebhookSubscription.objects.update_or_create(company=company,event='order.created',target_url='https://client.example/webhooks/orders',defaults={'signing_secret_hash':hashlib.sha256(b'demo-webhook-secret').hexdigest(),'is_active':True})
        IntegrationDelivery.objects.get_or_create(company=company,webhook=hook,event='order.created',defaults={'status':'Delivered','attempt_count':1,'payload':{'externalId':'WEB-44182'}})

        ProfitabilitySnapshot.objects.update_or_create(company=company,dimension='Customer',entity_key=str(customers['C-101'].id),period_from=date(2026,9,1),period_to=date(2026,9,21),defaults={'entity_name':customers['C-101'].name,'revenue':842000,'cogs':694000,'gross_profit':148000,'discounts':21400,'returns':8900,'delivery_cost':18200,'finance_cost':4200,'contribution_profit':95300,'margin_percent':Decimal('11.32')})
        CopilotActionProposal.objects.update_or_create(company=company,requested_by=users['OWNER'],title='Create collection tasks for outstanding customers',defaults={'action_type':'CREATE_COLLECTION_TASKS','rationale':'Demo proposal; owner or manager must approve before execution.','payload':{'customerIds':[customers['C-101'].id,customers['C-105'].id]},'risk_level':'Medium','requires_approval':True,'status':'Proposed'})

        # Growth v5 demo data: PIM, traceability, treasury, contracts, quality, planning, service, expenses, reports and observability.
        pim,_=ProductMasterProfile.objects.update_or_create(company=company,product=products['PC-25-RD'],defaults={'brand':'Polycab','manufacturer':'Polycab India','primary_uom':'coil','purchase_uom':'carton','sales_uom':'coil','uom_conversions':{'carton_to_coil':6},'alternate_barcodes':['8901002500017-A'],'mrp':2250,'dealer_price':2100,'distributor_price':2040,'batch_required':True,'minimum_stock':12,'maximum_stock':80,'reorder_quantity':24,'preferred_supplier':suppliers['S-001'],'data_quality_score':96,'governance_status':'Approved','updated_by':users['OWNER']})
        ProductMasterProfile.objects.update_or_create(company=company,product=products['HA-LED-12'],defaults={'brand':'Havells','manufacturer':'Havells India','primary_uom':'pcs','purchase_uom':'box','sales_uom':'pcs','uom_conversions':{'box_to_pcs':20},'mrp':170,'dealer_price':150,'distributor_price':145,'batch_required':True,'minimum_stock':30,'maximum_stock':250,'reorder_quantity':80,'preferred_supplier':suppliers['S-002'],'data_quality_score':82,'governance_status':'Approved','updated_by':users['OWNER']})
        ProductChangeRequest.objects.update_or_create(company=company,product=products['HA-LED-12'],change_type='GST update',status='Pending',defaults={'requested_changes':{'gst':12},'reason':'Tax master review','requested_by':users['ACCOUNTANT']})

        lot,_=InventoryLot.objects.update_or_create(company=company,product=products['HA-LED-12'],lot_no='LOT-260901',defaults={'warehouse':warehouses['WH-DEL'],'supplier':suppliers['S-002'],'batch_no':'HV2609A','manufactured_on':date(2026,8,15),'expiry_date':date(2028,9,1),'received_qty':120,'available_qty':86,'unit_cost':118,'status':'Available'})
        TraceabilityEvent.objects.get_or_create(company=company,product=products['HA-LED-12'],lot=lot,event_type='Received',reference='GRN-1082',defaults={'quantity':120,'created_by':users['WAREHOUSE']})
        serial,_=SerialUnit.objects.update_or_create(company=company,serial_no='LGFAN26090081',defaults={'product':products['LE-FAN-48'],'warehouse':warehouses['WH-DEL'],'status':'In Stock','warranty_until':date(2029,9,15)})
        TraceabilityEvent.objects.get_or_create(company=company,product=products['LE-FAN-48'],serial=serial,event_type='Serialized',reference='GRN-1088',defaults={'quantity':1,'created_by':users['WAREHOUSE']})

        hdfc,_=BankAccount.objects.update_or_create(company=company,name='HDFC Current',defaults={'bank_name':'HDFC Bank','account_last4':'8842','account_type':'Current','opening_balance':780000,'current_balance':840000})
        icici,_=BankAccount.objects.update_or_create(company=company,name='ICICI Current',defaults={'bank_name':'ICICI Bank','account_last4':'2218','account_type':'Current','opening_balance':300000,'current_balance':325000})
        BankTransaction.objects.update_or_create(company=company,bank_account=hdfc,reference='PAY-260921-01',defaults={'transaction_date':date(2026,9,21),'amount':58240,'transaction_type':'Credit','description':'R.K. Trading Co.','matching_status':'Unmatched'})
        BankTransaction.objects.update_or_create(company=company,bank_account=icici,reference='UTR992181',defaults={'transaction_date':date(2026,9,21),'amount':38400,'transaction_type':'Credit','description':'Unidentified receipt','matching_status':'Unmatched'})
        CashFlowForecast.objects.update_or_create(company=company,forecast_date=date(2026,9,22),defaults={'expected_inflow':91428,'expected_outflow':68857,'projected_balance':1259571,'source_snapshot':{'mode':'demo'}})

        agreement,_=RateAgreement.objects.update_or_create(company=company,agreement_no='AGR-2026-014',defaults={'customer':customers['C-102'],'title':'FY27 Electrical Rate Contract','start_date':date(2026,10,1),'end_date':date(2027,3,31),'status':'Active','minimum_monthly_purchase':500000,'credit_days':45,'created_by':users['MANAGER']})
        RateAgreementItem.objects.update_or_create(agreement=agreement,product=products['PC-25-RD'],defaults={'rate':1980,'minimum_qty':10,'escalation_percent':2})
        Tender.objects.update_or_create(company=company,tender_no='TND-2609-18',defaults={'customer':customers['C-104'],'title':'Noida Commercial Tower Electrical Package','due_date':date(2026,10,5),'expected_value':950000,'status':'Draft','terms':{'paymentDays':45}})

        inspection,_=QualityInspection.objects.update_or_create(company=company,inspection_no='QC-260921-01',defaults={'inspection_type':'Incoming','product':products['HA-LED-12'],'warehouse':warehouses['WH-DEL'],'supplier':suppliers['S-002'],'quantity_received':200,'quantity_inspected':20,'quantity_passed':18,'quantity_rejected':2,'quantity_quarantined':2,'status':'Completed','checklist':{'physicalDamage':2},'inspected_by':users['WAREHOUSE'],'inspected_at':timezone.now()})
        QuarantineStock.objects.update_or_create(company=company,inspection=inspection,product=products['HA-LED-12'],warehouse=warehouses['WH-DEL'],defaults={'quantity':2,'reason':'Physical damage','status':'Quarantined'})

        scenario,_=SupplyPlanScenario.objects.update_or_create(company=company,name='October base plan',defaults={'horizon_days':30,'demand_multiplier':Decimal('1.0'),'supplier_delay_days':0,'status':'Generated','created_by':users['MANAGER']})
        ReplenishmentPlan.objects.update_or_create(company=company,scenario=scenario,product=products['PC-25-RD'],to_warehouse=warehouses['WH-DEL'],defaults={'from_warehouse':warehouses['WH-NOI'],'forecast_demand':80,'available_stock':7,'safety_stock':12,'transfer_qty':10,'purchase_qty':75,'recommendation':'Transfer then purchase','status':'Recommended'})

        ticket,_=ServiceTicket.objects.update_or_create(company=company,ticket_no='SRV-260921-08',defaults={'customer':customers['C-101'],'product':products['LE-FAN-48'],'serial':serial,'complaint':'Motor noise after installation','status':'In Service','warranty_valid':True,'warranty_until':date(2029,9,15),'technician':users['WAREHOUSE'],'diagnosis':'Bearing noise confirmed'})
        RMA.objects.update_or_create(company=company,rma_no='RMA-260921-03',defaults={'ticket':ticket,'action':'Replace','status':'Manufacturer Review','manufacturer_claim_amount':4200,'manufacturer_claim_status':'Submitted'})

        petty,_=PettyCashAccount.objects.update_or_create(company=company,name='Delhi Office Petty Cash',defaults={'branch':branch,'balance':72000})
        claim,_=ExpenseClaim.objects.update_or_create(company=company,claim_no='EXP-260921-11',defaults={'employee':users['SALES'],'branch':branch,'category':'Travel','amount':2450,'expense_date':date(2026,9,21),'payment_method':'UPI','description':'Customer visits - West Delhi','status':'Submitted'})
        PettyCashTransaction.objects.get_or_create(account=petty,transaction_date=date(2026,9,20),transaction_type='Debit',amount=1800,note='Approved loading expense',defaults={'created_by':users['ACCOUNTANT']})

        report,_=ReportDefinition.objects.update_or_create(company=company,name='Salesperson Brand Margin',defaults={'data_source':'Sales','dimensions':['Salesperson','Brand'],'measures':['Revenue','Gross Profit'],'filters':{'territory':'Delhi NCR'},'group_by':['Salesperson'],'owner':users['OWNER'],'is_shared':True})
        schedule,_=ScheduledReport.objects.update_or_create(company=company,report=report,defaults={'frequency':'Weekly','delivery_time':'09:00','weekdays':['Monday'],'recipients':['accounts@khanna.demo'],'output_format':'XLSX','is_active':True})
        ReportRun.objects.get_or_create(report=report,status='Completed',row_count=48,defaults={'schedule':schedule,'started_at':timezone.now(),'finished_at':timezone.now()})

        for service,category,status,latency,message in [('Django API','Internal','Healthy',42,'Operational'),('PostgreSQL','Internal','Healthy',18,'Operational'),('Redis / Queue','Internal','Healthy',8,'Operational'),('WhatsApp','Provider','Healthy',110,'Operational'),('GST IRP','Provider','Degraded',380,'Elevated latency'),('Payment Provider','Provider','Healthy',142,'Operational')]:
            ServiceHealth.objects.update_or_create(company=company,service_name=service,defaults={'category':category,'status':status,'latency_ms':latency,'message':message})
        BackgroundJob.objects.update_or_create(company=company,job_key='gst-sync-260921-1400',defaults={'job_type':'GST_SYNC','status':'Failed','attempts':3,'last_error':'Provider timeout','scheduled_at':timezone.now()})
        WebhookReplay.objects.update_or_create(company=company,source='WhatsApp',event_id='wamid.demo.182',defaults={'status':'Failed','attempts':2,'last_error':'Template unavailable','payload':{'demo':True}})
        AlertPolicy.objects.update_or_create(company=company,name='Failed jobs alert',defaults={'condition':'failed_jobs','threshold':1,'channels':['email','in-app'],'is_active':True})

        self.stdout.write(self.style.SUCCESS('SetuStock production-style demo data created.'))
