import json
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone
from .models import (
    Branch, Company, Customer, InventoryMovement, Order, Product, Profile,
    PurchaseOrder, StockBalance, Supplier, Warehouse,
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
