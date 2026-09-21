from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        MANAGER = 'MANAGER', 'Manager'
        SALES = 'SALES', 'Sales'
        WAREHOUSE = 'WAREHOUSE', 'Warehouse'
        ACCOUNTANT = 'ACCOUNTANT', 'Accountant'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SALES)
    business_name = models.CharField(max_length=160, default='Khanna Electrical Distributors')

    def __str__(self):
        return f'{self.user.username} - {self.role}'

class Product(models.Model):
    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=100, blank=True)
    stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit = models.CharField(max_length=30, default='pcs')
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sell_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    location = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.sku} - {self.name}'

class Customer(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=160)
    city = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    gstin = models.CharField(max_length=20, blank=True)
    outstanding = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    class Status(models.TextChoices):
        PROCESSING = 'Processing', 'Processing'
        PACKED = 'Packed', 'Packed'
        READY = 'Ready', 'Ready'
        DISPATCHED = 'Dispatched', 'Dispatched'

    class PaymentStatus(models.TextChoices):
        PAID = 'Paid', 'Paid'
        CREDIT = 'Credit', 'Credit'
        OVERDUE = 'Overdue', 'Overdue'

    order_no = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.CREDIT)
    order_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order_no


class Invoice(models.Model):
    class Status(models.TextChoices):
        PAID = 'Paid', 'Paid'
        UNPAID = 'Unpaid', 'Unpaid'
        CREDIT = 'Credit', 'Credit'

    invoice_no = models.CharField(max_length=40, unique=True)
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name='invoice')
    gstin = models.CharField(max_length=20, blank=True)
    taxable_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cgst = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    igst = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)
    invoice_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_no

class Supplier(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=160)
    city = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    gstin = models.CharField(max_length=20, blank=True)
    outstanding = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        SENT = 'Sent', 'Sent'
        PARTIAL = 'Partial', 'Partial'
        RECEIVED = 'Received', 'Received'

    po_no = models.CharField(max_length=40, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.po_no


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchase_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    received_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class GoodsReceipt(models.Model):
    grn_no = models.CharField(max_length=40, unique=True)
    purchase = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='receipts')
    received_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.grn_no

class LedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        INVOICE = 'Invoice', 'Invoice'
        PAYMENT = 'Payment', 'Payment'
        CREDIT_NOTE = 'Credit Note', 'Credit Note'
        ADJUSTMENT = 'Adjustment', 'Adjustment'

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='ledger_entries')
    entry_type = models.CharField(max_length=20, choices=EntryType.choices)
    reference = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    entry_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.customer.code} {self.reference}'

class Warehouse(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=240, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class StockBalance(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_balances')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='warehouse_balances')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reserved = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['warehouse', 'product'], name='unique_warehouse_product')]


class StockTransfer(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        IN_TRANSIT = 'In Transit', 'In Transit'
        RECEIVED = 'Received', 'Received'

    transfer_no = models.CharField(max_length=40, unique=True)
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='outgoing_transfers')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='incoming_transfers')
    transfer_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)


class StockTransferItem(models.Model):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='transfer_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
