from django.contrib.auth.models import User
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=80, unique=True)
    gstin = models.CharField(max_length=20, blank=True)
    pan = models.CharField(max_length=16, blank=True)
    state = models.CharField(max_length=100, default='Delhi')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    bank_name = models.CharField(max_length=120, blank=True)
    bank_account = models.CharField(max_length=40, blank=True)
    ifsc = models.CharField(max_length=20, blank=True)
    upi_id = models.CharField(max_length=120, blank=True)
    logo_url = models.URLField(blank=True)
    invoice_prefix = models.CharField(max_length=20, default='INV')
    financial_year_start = models.PositiveSmallIntegerField(default=4)
    timezone = models.CharField(max_length=64, default='Asia/Kolkata')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Branch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=140)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    gstin = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'code'], name='unique_company_branch_code')]

    def __str__(self):
        return f'{self.company.name} / {self.name}'


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
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='profiles', null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, related_name='profiles', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    extra_permissions = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.role}'


class AuthSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_sessions')
    token_id = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    user_agent = models.CharField(max_length=240, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    @property
    def active(self):
        from django.utils import timezone
        return not self.revoked_at and self.expires_at > timezone.now()


class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    sku = models.CharField(max_length=40)
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=100, blank=True)
    stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit = models.CharField(max_length=30, default='pcs')
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sell_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    location = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    barcode = models.CharField(max_length=80, null=True, blank=True)
    qr_code = models.CharField(max_length=160, blank=True)
    hsn_code = models.CharField(max_length=20, blank=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    image_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'sku'], name='unique_company_product_sku'),
            models.UniqueConstraint(fields=['company', 'barcode'], name='unique_company_product_barcode'),
        ]

    def __str__(self):
        return f'{self.sku} - {self.name}'


class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers', null=True, blank=True)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=160)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, default='Delhi')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    gstin = models.CharField(max_length=20, blank=True)
    outstanding = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'code'], name='unique_company_customer_code')]

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouses', null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, related_name='warehouses', null=True, blank=True)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=240, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'code'], name='unique_company_warehouse_code')]

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        CONFIRMED = 'Confirmed', 'Confirmed'
        PROCESSING = 'Processing', 'Processing'
        PACKED = 'Packed', 'Packed'
        READY = 'Ready', 'Ready'
        DISPATCHED = 'Dispatched', 'Dispatched'
        CANCELLED = 'Cancelled', 'Cancelled'

    class PaymentStatus(models.TextChoices):
        PAID = 'Paid', 'Paid'
        PARTIAL = 'Partial', 'Partial'
        CREDIT = 'Credit', 'Credit'
        OVERDUE = 'Overdue', 'Overdue'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, related_name='orders', null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='orders', null=True, blank=True)
    order_no = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.CREDIT)
    order_date = models.DateField()
    notes = models.TextField(blank=True)
    stock_reserved = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_orders', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_no


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    taxable_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)


class Invoice(models.Model):
    class Status(models.TextChoices):
        PAID = 'Paid', 'Paid'
        PARTIAL = 'Partial', 'Partial'
        UNPAID = 'Unpaid', 'Unpaid'
        CREDIT = 'Credit', 'Credit'
        CANCELLED = 'Cancelled', 'Cancelled'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices', null=True, blank=True)
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
    due_date = models.DateField(null=True, blank=True)
    place_of_supply = models.CharField(max_length=100, blank=True)
    supply_type = models.CharField(max_length=20, default='Intra-state')
    e_invoice_irn = models.CharField(max_length=100, blank=True)
    e_invoice_status = models.CharField(max_length=30, default='Not generated')
    terms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    qr_payload = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.invoice_no


class Quotation(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        SENT = 'Sent', 'Sent'
        ACCEPTED = 'Accepted', 'Accepted'
        REJECTED = 'Rejected', 'Rejected'
        CONVERTED = 'Converted', 'Converted'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='quotations')
    quote_no = models.CharField(max_length=40, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='quotations')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='quotations', null=True, blank=True)
    quote_date = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    converted_order = models.OneToOneField(Order, on_delete=models.SET_NULL, related_name='source_quotation', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='quotation_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)


class Supplier(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='suppliers', null=True, blank=True)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=160)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, default='Delhi')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    gstin = models.CharField(max_length=20, blank=True)
    outstanding = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'code'], name='unique_company_supplier_code')]

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        APPROVED = 'Approved', 'Approved'
        SENT = 'Sent', 'Sent'
        PARTIAL = 'Partial', 'Partial'
        RECEIVED = 'Received', 'Received'
        CANCELLED = 'Cancelled', 'Cancelled'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_orders', null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, related_name='purchase_orders', null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='purchase_orders', null=True, blank=True)
    po_no = models.CharField(max_length=40, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='approved_purchase_orders', null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_purchase_orders', null=True, blank=True)
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
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='goods_receipts', null=True, blank=True)
    received_date = models.DateField()
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='goods_receipts', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.grn_no


class GoodsReceiptItem(models.Model):
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='items')
    purchase_item = models.ForeignKey(PurchaseItem, on_delete=models.PROTECT, related_name='receipt_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)


class LedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        INVOICE = 'Invoice', 'Invoice'
        PAYMENT = 'Payment', 'Payment'
        CREDIT_NOTE = 'Credit Note', 'Credit Note'
        ADJUSTMENT = 'Adjustment', 'Adjustment'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ledger_entries', null=True, blank=True)
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


class SupplierLedgerEntry(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supplier_ledger_entries')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='ledger_entries')
    entry_type = models.CharField(max_length=30)
    reference = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    entry_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = 'Cash', 'Cash'
        UPI = 'UPI', 'UPI'
        BANK = 'Bank', 'Bank transfer'
        CHEQUE = 'Cheque', 'Cheque'
        OTHER = 'Other', 'Other'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payments')
    receipt_no = models.CharField(max_length=40, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, related_name='payments', null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.BANK)
    reference = models.CharField(max_length=80, blank=True)
    payment_date = models.DateField()
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SupplierPayment(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supplier_payments')
    payment_no = models.CharField(max_length=40, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='payments')
    purchase = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, related_name='payments', null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=20, default='Bank')
    reference = models.CharField(max_length=80, blank=True)
    payment_date = models.DateField()
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class StockBalance(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_balances')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='warehouse_balances')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reserved = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['warehouse', 'product'], name='unique_warehouse_product')]


class InventoryMovement(models.Model):
    class MovementType(models.TextChoices):
        OPENING = 'Opening', 'Opening'
        PURCHASE = 'Purchase', 'Purchase receipt'
        SALE = 'Sale', 'Sales dispatch'
        SALES_RETURN = 'Sales Return', 'Sales return'
        PURCHASE_RETURN = 'Purchase Return', 'Purchase return'
        TRANSFER_OUT = 'Transfer Out', 'Transfer out'
        TRANSFER_IN = 'Transfer In', 'Transfer in'
        ADJUSTMENT = 'Adjustment', 'Adjustment'
        RESERVATION = 'Reservation', 'Reservation'
        RELEASE = 'Release', 'Reservation release'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='inventory_movements')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='inventory_movements')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='inventory_movements')
    movement_type = models.CharField(max_length=30, choices=MovementType.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=60)
    notes = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class StockTransfer(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        APPROVED = 'Approved', 'Approved'
        IN_TRANSIT = 'In Transit', 'In Transit'
        RECEIVED = 'Received', 'Received'
        CANCELLED = 'Cancelled', 'Cancelled'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_transfers', null=True, blank=True)
    transfer_no = models.CharField(max_length=40, unique=True)
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='outgoing_transfers')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='incoming_transfers')
    transfer_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_stock_transfers', null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='approved_stock_transfers', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class StockTransferItem(models.Model):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='transfer_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class BarcodeScanLog(models.Model):
    class Action(models.TextChoices):
        LOOKUP = 'Lookup', 'Lookup'
        STOCK_IN = 'Stock In', 'Stock In'
        STOCK_OUT = 'Stock Out', 'Stock Out'
        COUNT = 'Count', 'Count'

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='scan_logs')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='scan_logs', null=True, blank=True)
    action = models.CharField(max_length=20, choices=Action.choices, default=Action.LOOKUP)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    scanned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='barcode_scans')
    scanned_at = models.DateTimeField(auto_now_add=True)


class WhatsAppMessage(models.Model):
    class Direction(models.TextChoices):
        INBOUND = 'Inbound', 'Inbound'
        OUTBOUND = 'Outbound', 'Outbound'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='whatsapp_messages', null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='whatsapp_messages')
    direction = models.CharField(max_length=10, choices=Direction.choices)
    message = models.TextField()
    template_name = models.CharField(max_length=120, blank=True)
    provider_message_id = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=20, default='Delivered')
    created_at = models.DateTimeField(auto_now_add=True)


class WhatsAppOrderDraft(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        QUOTED = 'Quoted', 'Quoted'
        CONFIRMED = 'Confirmed', 'Confirmed'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='whatsapp_order_drafts', null=True, blank=True)
    draft_no = models.CharField(max_length=40, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='whatsapp_order_drafts')
    raw_message = models.TextField()
    parsed_items = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    estimated_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class TaxNote(models.Model):
    class NoteType(models.TextChoices):
        CREDIT = 'Credit Note', 'Credit Note'
        DEBIT = 'Debit Note', 'Debit Note'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tax_notes', null=True, blank=True)
    note_no = models.CharField(max_length=40, unique=True)
    note_type = models.CharField(max_length=20, choices=NoteType.choices)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='tax_notes')
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='tax_notes', null=True, blank=True)
    taxable_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    note_date = models.DateField()
    reason = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PriceList(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='price_lists', null=True, blank=True)
    name = models.CharField(max_length=120)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='price_lists', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


class PriceRule(models.Model):
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='rules')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_rules')
    min_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    scheme_text = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ['product__name', 'min_quantity']


class StockAdjustment(models.Model):
    class AdjustmentType(models.TextChoices):
        DAMAGE = 'Damaged', 'Damaged'
        COUNT = 'Count correction', 'Count correction'
        EXPIRY = 'Expired', 'Expired'
        OTHER = 'Other', 'Other'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_adjustments', null=True, blank=True)
    adjustment_no = models.CharField(max_length=40, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='stock_adjustments')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='stock_adjustments')
    adjustment_type = models.CharField(max_length=30, choices=AdjustmentType.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=240)
    adjustment_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ReturnOrder(models.Model):
    class ReturnType(models.TextChoices):
        SALES = 'Sales Return', 'Sales Return'
        PURCHASE = 'Purchase Return', 'Purchase Return'

    class Status(models.TextChoices):
        OPEN = 'Open', 'Open'
        INSPECTED = 'Inspected', 'Inspected'
        COMPLETED = 'Completed', 'Completed'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='returns', null=True, blank=True)
    return_no = models.CharField(max_length=40, unique=True)
    return_type = models.CharField(max_length=20, choices=ReturnType.choices)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='returns', null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='returns', null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='returns')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    return_date = models.DateField()
    reason = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


class ReturnItem(models.Model):
    return_order = models.ForeignKey(ReturnOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='return_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    condition = models.CharField(max_length=30, default='Resellable')


class SalesVisit(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'Planned', 'Planned'
        VISITED = 'Visited', 'Visited'
        MISSED = 'Missed', 'Missed'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales_visits', null=True, blank=True)
    salesperson = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_visits')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales_visits')
    visit_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    territory = models.CharField(max_length=100, blank=True)
    order_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    collection_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.CharField(max_length=240, blank=True)


class SalesTarget(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales_targets', null=True, blank=True)
    salesperson = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_targets')
    month = models.DateField()
    target_sales = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    target_collection = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['salesperson', 'month'], name='unique_sales_target_month')]


class ReorderSuggestion(models.Model):
    class Risk(models.TextChoices):
        HIGH = 'High', 'High'
        MEDIUM = 'Medium', 'Medium'
        LOW = 'Low', 'Low'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reorder_suggestions')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='reorder_suggestions')
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_daily_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lead_time_days = models.PositiveIntegerField(default=1)
    suggested_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    days_cover = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    risk = models.CharField(max_length=10, choices=Risk.choices, default=Risk.MEDIUM)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['product', 'warehouse'], name='unique_reorder_suggestion')]


class AuditLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='audit_logs')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='audit_logs', null=True, blank=True)
    action = models.CharField(max_length=40)
    entity_type = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80)
    summary = models.CharField(max_length=240)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Notification(models.Model):
    class Level(models.TextChoices):
        INFO = 'info', 'Info'
        WARNING = 'warning', 'Warning'
        CRITICAL = 'critical', 'Critical'
        SUCCESS = 'success', 'Success'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    title = models.CharField(max_length=140)
    message = models.CharField(max_length=300)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.INFO)
    module = models.CharField(max_length=40, blank=True)
    entity_id = models.CharField(max_length=80, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Attachment(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='attachments')
    module = models.CharField(max_length=40)
    entity_id = models.CharField(max_length=80)
    file = models.FileField(upload_to='attachments/%Y/%m/')
    original_name = models.CharField(max_length=200)
    content_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='uploaded_attachments', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CustomerPortalAccess(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='portal_access')
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='portal_access')
    email = models.EmailField()
    pin_hash = models.CharField(max_length=180)
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'email'], name='unique_company_portal_email')]


class CustomerPortalOrder(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'Submitted', 'Submitted'
        ACCEPTED = 'Accepted', 'Accepted'
        REJECTED = 'Rejected', 'Rejected'
        CONVERTED = 'Converted', 'Converted'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='portal_orders')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='portal_orders')
    request_no = models.CharField(max_length=40, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    items = models.JSONField(default=list)
    estimated_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    converted_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='portal_requests')
    created_at = models.DateTimeField(auto_now_add=True)


class DeliveryRun(models.Model):
    class Status(models.TextChoices):
        PLANNED='Planned','Planned'; LOADING='Loading','Loading'; OUT='Out for Delivery','Out for Delivery'; COMPLETED='Completed','Completed'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='delivery_runs')
    run_no=models.CharField(max_length=40,unique=True)
    route_name=models.CharField(max_length=120)
    driver_name=models.CharField(max_length=120)
    driver_phone=models.CharField(max_length=20,blank=True)
    vehicle_no=models.CharField(max_length=30,blank=True)
    delivery_date=models.DateField()
    status=models.CharField(max_length=30,choices=Status.choices,default=Status.PLANNED)
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class DeliveryStop(models.Model):
    class Status(models.TextChoices):
        PENDING='Pending','Pending'; DELIVERED='Delivered','Delivered'; FAILED='Failed','Failed'
    run=models.ForeignKey(DeliveryRun,on_delete=models.CASCADE,related_name='stops')
    order=models.ForeignKey(Order,on_delete=models.PROTECT,related_name='delivery_stops')
    sequence=models.PositiveIntegerField(default=1)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.PENDING)
    cod_amount=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    failure_reason=models.CharField(max_length=240,blank=True)
    delivered_at=models.DateTimeField(null=True,blank=True)

class DeliveryProof(models.Model):
    stop=models.OneToOneField(DeliveryStop,on_delete=models.CASCADE,related_name='proof')
    otp_verified=models.BooleanField(default=False)
    receiver_name=models.CharField(max_length=120,blank=True)
    signature_data=models.TextField(blank=True)
    photo_url=models.URLField(blank=True)
    note=models.CharField(max_length=240,blank=True)
    captured_at=models.DateTimeField(auto_now_add=True)


class ApprovalPolicy(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='approval_policies')
    key=models.CharField(max_length=60)
    label=models.CharField(max_length=140)
    threshold=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    approver_role=models.CharField(max_length=20,default='MANAGER')
    is_active=models.BooleanField(default=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['company','key'],name='unique_company_approval_policy')]

class ApprovalRequest(models.Model):
    class Status(models.TextChoices): PENDING='Pending','Pending'; APPROVED='Approved','Approved'; REJECTED='Rejected','Rejected'; CANCELLED='Cancelled','Cancelled'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='approval_requests')
    policy=models.ForeignKey(ApprovalPolicy,on_delete=models.PROTECT,related_name='requests',null=True,blank=True)
    request_no=models.CharField(max_length=40,unique=True)
    entity_type=models.CharField(max_length=60)
    entity_id=models.CharField(max_length=80)
    title=models.CharField(max_length=180)
    amount=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    payload=models.JSONField(default=dict,blank=True)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.PENDING)
    requested_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='approval_requests_made')
    decided_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='approval_requests_decided')
    decision_note=models.CharField(max_length=240,blank=True)
    created_at=models.DateTimeField(auto_now_add=True); decided_at=models.DateTimeField(null=True,blank=True)


class PurchaseInvoiceCapture(models.Model):
    class Status(models.TextChoices): UPLOADED='Uploaded','Uploaded'; EXTRACTED='Extracted','Extracted'; REVIEWED='Reviewed','Reviewed'; POSTED='Posted','Posted'; FAILED='Failed','Failed'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='invoice_captures')
    supplier=models.ForeignKey(Supplier,on_delete=models.SET_NULL,null=True,blank=True,related_name='invoice_captures')
    file_name=models.CharField(max_length=200)
    file_url=models.URLField(blank=True)
    raw_text=models.TextField(blank=True)
    extracted_data=models.JSONField(default=dict,blank=True)
    confidence=models.DecimalField(max_digits=5,decimal_places=2,default=0)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.UPLOADED)
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)


class AccountingConnection(models.Model):
    class Provider(models.TextChoices): TALLY='TALLY','Tally'; ZOHO='ZOHO','Zoho Books'; CSV='CSV','CSV / Excel'
    company=models.OneToOneField(Company,on_delete=models.CASCADE,related_name='accounting_connection')
    provider=models.CharField(max_length=20,choices=Provider.choices,default=Provider.CSV)
    is_active=models.BooleanField(default=False)
    settings=models.JSONField(default=dict,blank=True)
    last_sync_at=models.DateTimeField(null=True,blank=True)
    updated_at=models.DateTimeField(auto_now=True)

class AccountingExportJob(models.Model):
    class Status(models.TextChoices): QUEUED='Queued','Queued'; READY='Ready','Ready'; FAILED='Failed','Failed'; SYNCED='Synced','Synced'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='accounting_exports')
    provider=models.CharField(max_length=20,default='CSV')
    export_no=models.CharField(max_length=40,unique=True)
    period_from=models.DateField(); period_to=models.DateField()
    voucher_count=models.PositiveIntegerField(default=0)
    payload=models.JSONField(default=list,blank=True)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.QUEUED)
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
