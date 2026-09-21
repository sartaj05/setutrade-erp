import json
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.test import Client, TestCase
from django.utils import timezone
from .models import (
    Branch, Company, Customer, InventoryMovement, Order, Product, Profile,
    PurchaseOrder, StockBalance, Supplier, Warehouse, SupplierPortalAccess, AutomationRule, ExternalChannel, DistributionNetwork, WarehouseBin,
)


class ProductionApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(name='Test Distribution Co.', slug='test-distribution', gstin='07ABCDE1234F1Z5')
        self.branch = Branch.objects.create(company=self.company, code='DEL', name='Delhi HQ', city='Delhi')
        self.owner = User.objects.create_user(
            username='owner-test', email='owner-test@example.com', password='test-password-123', first_name='Owner',
        )
        Profile.objects.create(user=self.owner, role='OWNER', business_name=self.company.name, company=self.company, branch=self.branch)
        self.warehouse = Warehouse.objects.create(company=self.company, branch=self.branch, code='WH1', name='Main Warehouse', city='Delhi')
        self.product = Product.objects.create(
            company=self.company, sku='SKU-1', name='Test Switch', purchase_price=Decimal('50'),
            sell_price=Decimal('100'), gst_rate=Decimal('18'), reorder_level=Decimal('5'), stock=Decimal('50'),
        )
        StockBalance.objects.create(warehouse=self.warehouse, product=self.product, quantity=Decimal('50'), reserved=0)
        self.customer = Customer.objects.create(company=self.company, code='C-1', name='Test Customer', state='Delhi', credit_limit=Decimal('50000'))
        self.supplier = Supplier.objects.create(company=self.company, code='S-1', name='Test Supplier', state='Delhi')
        self.token = self.login()['token']

    def post(self, path, payload, auth=True):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'} if auth else {}
        return self.client.post(path, data=json.dumps(payload), content_type='application/json', **headers)

    def patch(self, path, payload):
        return self.client.patch(path, data=json.dumps(payload), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def login(self):
        response = self.client.post(
            '/api/auth/login/', data=json.dumps({'email': self.owner.email, 'password': 'test-password-123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_health_and_login_return_tenant_context(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        payload = self.login()
        self.assertEqual(payload['user']['role'], 'OWNER')
        self.assertEqual(payload['user']['companyId'], self.company.id)
        self.assertIn('refreshToken', payload)
        self.assertIn('audit', payload['user']['permissions'])

    def test_tenant_isolation_and_same_reference_codes(self):
        other = Company.objects.create(name='Other Co.', slug='other-co')
        Product.objects.create(company=other, sku='SKU-1', name='Other Switch')
        Customer.objects.create(company=other, code='C-1', name='Other Customer')
        Warehouse.objects.create(company=other, code='WH1', name='Other Warehouse')
        Supplier.objects.create(company=other, code='S-1', name='Other Supplier')
        response = self.client.get('/api/products/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['name'] for row in response.json()['products']], ['Test Switch'])

    def test_sales_order_reserves_and_dispatches_stock(self):
        response = self.post('/api/orders/', {
            'customerId': self.customer.id, 'warehouseId': self.warehouse.id, 'confirm': True,
            'items': [{'product_id': self.product.id, 'quantity': 4, 'unit_price': 100}],
        })
        self.assertEqual(response.status_code, 201, response.content)
        order_id = response.json()['order']['pk']
        balance = StockBalance.objects.get(warehouse=self.warehouse, product=self.product)
        self.assertEqual(balance.reserved, Decimal('4.00'))
        response = self.post(f'/api/orders/{order_id}/action/', {'action': 'dispatch'})
        self.assertEqual(response.status_code, 200, response.content)
        balance.refresh_from_db(); self.product.refresh_from_db()
        self.assertEqual(balance.quantity, Decimal('46.00'))
        self.assertEqual(balance.reserved, Decimal('0.00'))
        self.assertEqual(self.product.stock, Decimal('46.00'))
        self.assertTrue(InventoryMovement.objects.filter(reference=response.json()['order']['id'], movement_type='Sale').exists())

    def test_purchase_requires_approval_then_grn_updates_stock(self):
        response = self.post('/api/purchases/', {
            'supplierId': self.supplier.id, 'warehouseId': self.warehouse.id,
            'items': [{'productId': self.product.id, 'quantity': 10, 'unitPrice': 45}],
        })
        self.assertEqual(response.status_code, 201, response.content)
        po_id = response.json()['purchase']['pk']
        blocked = self.post(f'/api/purchases/{po_id}/action/', {'action': 'receive'})
        self.assertEqual(blocked.status_code, 400)
        approved = self.post(f'/api/purchases/{po_id}/action/', {'action': 'approve'})
        self.assertEqual(approved.status_code, 200)
        received = self.post(f'/api/purchases/{po_id}/action/', {'action': 'receive'})
        self.assertEqual(received.status_code, 200, received.content)
        balance = StockBalance.objects.get(warehouse=self.warehouse, product=self.product)
        self.assertEqual(balance.quantity, Decimal('60.00'))
        po = PurchaseOrder.objects.get(pk=po_id)
        self.assertEqual(po.status, PurchaseOrder.Status.RECEIVED)
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.outstanding, Decimal('450.00'))

    def test_invoice_payment_and_ledger_workflow(self):
        order = self.post('/api/orders/', {
            'customerId': self.customer.id, 'warehouseId': self.warehouse.id,
            'items': [{'product_id': self.product.id, 'quantity': 2, 'unit_price': 100}],
        }).json()['order']
        invoice_response = self.post('/api/invoices/', {'orderId': order['pk'], 'invoiceDate': timezone.localdate().isoformat()})
        self.assertEqual(invoice_response.status_code, 201, invoice_response.content)
        invoice = invoice_response.json()['invoice']
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.outstanding, Decimal(str(invoice['total'])))
        payment_response = self.post('/api/payments/', {
            'partyType': 'customer', 'customerId': self.customer.id, 'amount': invoice['total'], 'method': 'UPI',
        })
        self.assertEqual(payment_response.status_code, 201, payment_response.content)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.outstanding, Decimal('0.00'))
        ledger = self.client.get('/api/ledger/', HTTP_AUTHORIZATION=f'Bearer {self.token}').json()['ledger']
        self.assertEqual(len(ledger), 2)

    def test_password_reset_and_session_revocation(self):
        reset_request = self.post('/api/auth/password-reset/request/', {'email': self.owner.email}, auth=False)
        self.assertEqual(reset_request.status_code, 200)
        reset = reset_request.json()['demoReset']
        confirm = self.post('/api/auth/password-reset/confirm/', {
            'uid': reset['uid'], 'token': reset['token'], 'newPassword': 'new-secure-password-456',
        }, auth=False)
        self.assertEqual(confirm.status_code, 200, confirm.content)
        old_session = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(old_session.status_code, 401)
        login = self.client.post('/api/auth/login/', data=json.dumps({'email': self.owner.email, 'password': 'new-secure-password-456'}), content_type='application/json')
        self.assertEqual(login.status_code, 200)

    def test_growth_modules_smoke(self):
        from django.contrib.auth.hashers import make_password
        from .models import ApprovalPolicy, CustomerPortalAccess, DeliveryRun
        CustomerPortalAccess.objects.create(company=self.company, customer=self.customer, email='dealer@example.com', pin_hash=make_password('1234'))
        portal = self.client.post('/api/portal/login/', data=json.dumps({'email':'dealer@example.com','pin':'1234'}), content_type='application/json')
        self.assertEqual(portal.status_code, 200, portal.content)
        portal_token = portal.json()['token']
        catalog = self.client.get('/api/portal/catalog/', HTTP_AUTHORIZATION=f'Portal {portal_token}')
        self.assertEqual(catalog.status_code, 200, catalog.content)

        run = self.post('/api/delivery/', {'action':'create-run','routeName':'Test route','driverName':'Driver','orderIds':[]})
        self.assertEqual(run.status_code, 201, run.content)
        self.assertTrue(DeliveryRun.objects.filter(company=self.company).exists())

        policy = ApprovalPolicy.objects.create(company=self.company, key='credit', label='Credit override', threshold=1000, approver_role='OWNER')
        approval = self.post('/api/approvals/', {'action':'request','policyKey':policy.key,'entityType':'Customer','entityId':str(self.customer.id),'title':'Credit override','amount':5000})
        self.assertEqual(approval.status_code, 201, approval.content)
        decision = self.post('/api/approvals/', {'action':'approve','id':approval.json()['id']})
        self.assertEqual(decision.status_code, 200, decision.content)

        ocr = self.post('/api/invoice-ocr/', {'fileName':'supplier.txt','rawText':'Invoice No: ABC-19 GSTIN 07ABCDE1234F1Z5 Date 21/09/2026 Grand Total 12,450.00'})
        self.assertEqual(ocr.status_code, 201, ocr.content)
        self.assertEqual(ocr.json()['capture']['data']['invoiceNumber'], 'ABC-19')

        accounting = self.post('/api/accounting/', {'action':'export','from':timezone.localdate().replace(day=1).isoformat(),'to':timezone.localdate().isoformat()})
        self.assertEqual(accounting.status_code, 201, accounting.content)

        offline = self.post('/api/sync/offline/', {'deviceId':'test','events':[{'id':'evt-1','type':'customer-note','payload':{'notes':'offline'}}]})
        self.assertEqual(offline.status_code, 200, offline.content)
        self.assertEqual(offline.json()['synced'], 1)

        billing = self.client.get('/api/subscription/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(billing.status_code, 200, billing.content)
        self.assertGreaterEqual(len(billing.json()['plans']), 3)

        forecast = self.client.get('/api/forecasting/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(forecast.status_code, 200, forecast.content)
        self.assertIn('forecasts', forecast.json())

        assistant = self.post('/api/assistant/', {'question':'What are month-to-date sales?'})
        self.assertEqual(assistant.status_code, 200, assistant.content)
        self.assertEqual(assistant.json()['intent'], 'sales')


    def test_growth_v3_collections_wms_and_automation(self):
        collection = self.post('/api/collections/', {'action':'task','customerId':self.customer.id,'amount':25000,'date':timezone.localdate().isoformat(),'priority':'High'})
        self.assertEqual(collection.status_code, 201, collection.content)
        rows = self.client.get('/api/collections/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(rows.status_code, 200, rows.content)
        self.assertEqual(rows.json()['summary']['openTasks'], 1)

        bin_response = self.post('/api/wms/', {'action':'create-bin','warehouseId':self.warehouse.id,'code':'A-01-01','zone':'Fast'})
        self.assertEqual(bin_response.status_code, 201, bin_response.content)
        self.assertTrue(WarehouseBin.objects.filter(warehouse=self.warehouse, code='A-01-01').exists())

        AutomationRule.objects.create(company=self.company,name='Test overdue rule',event='invoice.overdue',conditions={'outstanding':{'gte':1000}},actions=[{'type':'create_collection_task'}],created_by=self.owner)
        run = self.post('/api/automations/', {'action':'test','event':'invoice.overdue','payload':{'outstanding':2000,'customerId':self.customer.id},'entityType':'Customer','entityId':str(self.customer.id)})
        self.assertEqual(run.status_code, 200, run.content)
        self.assertEqual(run.json()['matched'], 1)

    def test_supplier_portal_channel_and_distribution_network(self):
        SupplierPortalAccess.objects.create(company=self.company,supplier=self.supplier,email='supplier-test@example.com',pin_hash=make_password('1234'))
        login = self.client.post('/api/supplier-portal/login/', data=json.dumps({'email':'supplier-test@example.com','pin':'1234'}), content_type='application/json')
        self.assertEqual(login.status_code, 200, login.content)
        supplier_token = login.json()['token']
        portal = self.client.get('/api/supplier-portal/', HTTP_AUTHORIZATION=f'Supplier {supplier_token}')
        self.assertEqual(portal.status_code, 200, portal.content)

        channel = self.post('/api/channels/', {'action':'create-channel','name':'Test Web','provider':'WEBSITE'})
        self.assertEqual(channel.status_code, 201, channel.content)
        ingest = self.post('/api/channels/', {'action':'ingest-order','channelId':channel.json()['id'],'externalId':'WEB-1','customerName':'Buyer','total':100,'items':[{'sku':self.product.sku,'quantity':1,'unitPrice':100}]})
        self.assertEqual(ingest.status_code, 201, ingest.content)
        duplicate = self.post('/api/channels/', {'action':'ingest-order','channelId':channel.json()['id'],'externalId':'WEB-1','customerName':'Buyer','total':100,'items':[]})
        self.assertEqual(duplicate.status_code, 200, duplicate.content)

        network = self.post('/api/distribution-networks/', {'action':'create-network','name':'Test Network','code':'TEST-NET'})
        self.assertEqual(network.status_code, 201, network.content)
        self.assertTrue(DistributionNetwork.objects.filter(owner_company=self.company, code='TEST-NET').exists())

    def test_growth_v4_strategy_modules(self):
        self.customer.outstanding = Decimal('25000'); self.customer.credit_limit = Decimal('50000'); self.customer.save(update_fields=['outstanding','credit_limit'])
        crm = self.post('/api/crm/', {'action':'lead','name':'Prospect','business':'Prospect Traders','value':125000})
        self.assertEqual(crm.status_code, 201, crm.content)
        scheme = self.post('/api/schemes/', {'action':'create-scheme','supplierId':self.supplier.id,'name':'Test rebate','start':timezone.localdate().isoformat(),'end':timezone.localdate().isoformat(),'rebate':2})
        self.assertEqual(scheme.status_code, 201, scheme.content)
        gst = self.post('/api/gst-cockpit/', {'invoiceNo':'SUP-T-1','supplierId':self.supplier.id,'booksTax':1800,'portalTax':1700})
        self.assertEqual(gst.status_code, 201, gst.content)
        procurement = self.post('/api/procurement-intelligence/', {'action':'recalculate'})
        self.assertEqual(procurement.status_code, 200, procurement.content)
        vehicle = self.post('/api/fleet-routes/', {'action':'vehicle','vehicleNo':'DL-TEST-1','capacityKg':1000,'costPerKm':15})
        self.assertEqual(vehicle.status_code, 201, vehicle.content)
        route = self.post('/api/fleet-routes/', {'action':'optimize','vehicleId':vehicle.json()['id'],'warehouseId':self.warehouse.id})
        self.assertEqual(route.status_code, 201, route.content)
        credit = self.post('/api/credit-risk/', {'action':'rescore'})
        self.assertEqual(credit.status_code, 200, credit.content)
        mfa = self.post('/api/security-center/', {'action':'enable-mfa'})
        self.assertEqual(mfa.status_code, 200, mfa.content)
        key = self.post('/api/integrations/', {'action':'api-key','name':'test-api','scopes':['orders:write']})
        self.assertEqual(key.status_code, 201, key.content)
        public = self.client.post('/api/public/v1/order-intake/', data=json.dumps({'externalId':'API-T-1','customerName':'API Buyer','total':100}), content_type='application/json', HTTP_X_SETUSTOCK_KEY=key.json()['apiKey'])
        self.assertEqual(public.status_code, 201, public.content)
        bi = self.client.get('/api/executive-bi/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(bi.status_code, 200, bi.content)
        proposal = self.post('/api/copilot-actions/', {'action':'propose','prompt':'Create collection tasks for overdue customers'})
        self.assertEqual(proposal.status_code, 201, proposal.content)
        execute = self.post('/api/copilot-actions/', {'action':'approve','id':proposal.json()['id']})
        self.assertEqual(execute.status_code, 200, execute.content)
        self.assertEqual(execute.json()['status'], 'Executed')

    def test_growth_v5_operational_modules(self):
        pim = self.post('/api/product-master/', {'action':'refresh-quality'})
        self.assertEqual(pim.status_code, 200, pim.content)
        self.assertGreaterEqual(pim.json()['updated'], 1)

        lot = self.post('/api/traceability/', {'action':'receive-lot','productId':self.product.id,'warehouseId':self.warehouse.id,'supplierId':self.supplier.id,'lotNo':'LOT-T-1','quantity':10})
        self.assertEqual(lot.status_code, 201, lot.content)

        treasury = self.post('/api/treasury/', {'action':'generate-forecast'})
        self.assertEqual(treasury.status_code, 200, treasury.content)
        self.assertEqual(treasury.json()['days'], 7)

        agreement = self.post('/api/contracts/', {'action':'agreement','customerId':self.customer.id,'title':'Test contract','minimumMonthly':10000})
        self.assertEqual(agreement.status_code, 201, agreement.content)
        tender = self.post('/api/contracts/', {'action':'tender','customerId':self.customer.id,'title':'Test tender','value':25000})
        self.assertEqual(tender.status_code, 201, tender.content)

        inspection = self.post('/api/quality/', {'action':'inspection','productId':self.product.id,'warehouseId':self.warehouse.id,'supplierId':self.supplier.id,'quantity':20})
        self.assertEqual(inspection.status_code, 201, inspection.content)
        complete = self.post('/api/quality/', {'action':'complete','inspectionId':inspection.json()['id'],'inspected':5,'passed':4,'rejected':1,'quarantined':1})
        self.assertEqual(complete.status_code, 200, complete.content)

        plan = self.post('/api/supply-planning/', {'action':'generate','name':'Test scenario','horizon':30,'demandMultiplier':1.1})
        self.assertEqual(plan.status_code, 201, plan.content)
        self.assertGreaterEqual(plan.json()['plans'], 1)

        ticket = self.post('/api/service-rma/', {'action':'ticket','customerId':self.customer.id,'productId':self.product.id,'complaint':'Test complaint'})
        self.assertEqual(ticket.status_code, 201, ticket.content)
        rma = self.post('/api/service-rma/', {'action':'rma','ticketId':ticket.json()['id'],'rmaAction':'Repair','claimAmount':500})
        self.assertEqual(rma.status_code, 201, rma.content)

        claim = self.post('/api/expenses/', {'action':'submit','category':'Travel','amount':500,'description':'Test claim'})
        self.assertEqual(claim.status_code, 201, claim.content)
        approve = self.post('/api/expenses/', {'action':'approve','claimId':claim.json()['id']})
        self.assertEqual(approve.status_code, 200, approve.content)

        report = self.post('/api/report-builder/', {'action':'create-report','name':'Test Sales Report','source':'Sales','dimensions':['Customer'],'measures':['Revenue']})
        self.assertEqual(report.status_code, 201, report.content)
        run = self.post('/api/report-builder/', {'action':'run','reportId':report.json()['id']})
        self.assertEqual(run.status_code, 201, run.content)

        heartbeat = self.post('/api/operations-center/', {'action':'heartbeat'})
        self.assertEqual(heartbeat.status_code, 200, heartbeat.content)
        self.assertGreaterEqual(heartbeat.json()['checked'], 5)
