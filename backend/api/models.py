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


class OfflineSyncReceipt(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='offline_sync_receipts')
    event_id=models.CharField(max_length=80)
    event_type=models.CharField(max_length=50)
    payload=models.JSONField(default=dict,blank=True)
    device_id=models.CharField(max_length=100,blank=True)
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    synced_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['company','event_id'],name='unique_company_offline_event')]


class SubscriptionPlan(models.Model):
    code=models.CharField(max_length=30,unique=True)
    name=models.CharField(max_length=80)
    monthly_price=models.DecimalField(max_digits=10,decimal_places=2)
    annual_price=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    user_limit=models.PositiveIntegerField(default=3)
    branch_limit=models.PositiveIntegerField(default=1)
    warehouse_limit=models.PositiveIntegerField(default=1)
    features=models.JSONField(default=list,blank=True)
    is_active=models.BooleanField(default=True)

class CompanySubscription(models.Model):
    class Status(models.TextChoices): TRIAL='Trial','Trial'; ACTIVE='Active','Active'; PAST_DUE='Past Due','Past Due'; CANCELLED='Cancelled','Cancelled'
    company=models.OneToOneField(Company,on_delete=models.CASCADE,related_name='subscription')
    plan=models.ForeignKey(SubscriptionPlan,on_delete=models.PROTECT,related_name='subscriptions')
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.TRIAL)
    started_at=models.DateField(); current_period_end=models.DateField()
    trial_end=models.DateField(null=True,blank=True)
    external_customer_id=models.CharField(max_length=120,blank=True)
    cancel_at_period_end=models.BooleanField(default=False)
    updated_at=models.DateTimeField(auto_now=True)

class SubscriptionInvoice(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='subscription_invoices')
    subscription=models.ForeignKey(CompanySubscription,on_delete=models.CASCADE,related_name='invoices')
    invoice_no=models.CharField(max_length=40,unique=True)
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    tax=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    status=models.CharField(max_length=20,default='Open')
    due_date=models.DateField(); paid_at=models.DateTimeField(null=True,blank=True)
    payment_reference=models.CharField(max_length=120,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)


class DemandForecast(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='demand_forecasts')
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='demand_forecasts')
    warehouse=models.ForeignKey(Warehouse,on_delete=models.SET_NULL,null=True,blank=True,related_name='demand_forecasts')
    horizon_days=models.PositiveIntegerField(default=30)
    avg_daily_demand=models.DecimalField(max_digits=12,decimal_places=3,default=0)
    trend_percent=models.DecimalField(max_digits=8,decimal_places=2,default=0)
    forecast_quantity=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    safety_stock=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    recommended_purchase=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    confidence=models.DecimalField(max_digits=5,decimal_places=2,default=0)
    generated_at=models.DateTimeField(auto_now=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['company','product','warehouse','horizon_days'],name='unique_company_product_forecast')]


class AssistantThread(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='assistant_threads')
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='assistant_threads')
    title=models.CharField(max_length=160,default='Business assistant')
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)

class AssistantMessage(models.Model):
    thread=models.ForeignKey(AssistantThread,on_delete=models.CASCADE,related_name='messages')
    role=models.CharField(max_length=20,choices=[('user','User'),('assistant','Assistant')])
    content=models.TextField()
    intent=models.CharField(max_length=60,blank=True)
    data=models.JSONField(default=dict,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

# --- Growth v3 / Phase 11: automated collections and reconciliation ---
class PaymentTransaction(models.Model):
    class Status(models.TextChoices):
        UNMATCHED = 'Unmatched', 'Unmatched'
        PARTIAL = 'Partial', 'Partial'
        MATCHED = 'Matched', 'Matched'
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payment_transactions')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='payment_transactions')
    reference = models.CharField(max_length=80)
    method = models.CharField(max_length=30, default='UPI')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    transaction_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNMATCHED)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['company', 'reference'], name='unique_company_payment_reference')]


class PaymentAllocation(models.Model):
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name='allocations')
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payment_allocations')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class PaymentPromise(models.Model):
    class Status(models.TextChoices):
        OPEN='Open','Open'; KEPT='Kept','Kept'; BROKEN='Broken','Broken'; CANCELLED='Cancelled','Cancelled'
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payment_promises')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='payment_promises')
    promised_amount = models.DecimalField(max_digits=14, decimal_places=2)
    promised_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    notes = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CollectionTask(models.Model):
    class Status(models.TextChoices):
        OPEN='Open','Open'; CONTACTED='Contacted','Contacted'; COLLECTED='Collected','Collected'; RESCHEDULED='Rescheduled','Rescheduled'
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='collection_tasks')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='collection_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='collection_tasks')
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    priority = models.CharField(max_length=20, default='Normal')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    notes = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# --- Growth v3 / Phase 12: advanced warehouse management ---
class WarehouseBin(models.Model):
    warehouse=models.ForeignKey(Warehouse,on_delete=models.CASCADE,related_name='bins')
    code=models.CharField(max_length=40)
    zone=models.CharField(max_length=60,blank=True)
    capacity=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    is_active=models.BooleanField(default=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['warehouse','code'],name='unique_warehouse_bin_code')]

class BinStock(models.Model):
    bin=models.ForeignKey(WarehouseBin,on_delete=models.CASCADE,related_name='stocks')
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='bin_stocks')
    quantity=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    class Meta: constraints=[models.UniqueConstraint(fields=['bin','product'],name='unique_bin_product')]

class PickList(models.Model):
    class Status(models.TextChoices): DRAFT='Draft','Draft'; RELEASED='Released','Released'; PICKING='Picking','Picking'; COMPLETE='Complete','Complete'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='pick_lists')
    warehouse=models.ForeignKey(Warehouse,on_delete=models.PROTECT,related_name='pick_lists')
    pick_no=models.CharField(max_length=40,unique=True)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.DRAFT)
    assigned_to=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='pick_lists')
    created_at=models.DateTimeField(auto_now_add=True)

class PickListItem(models.Model):
    pick_list=models.ForeignKey(PickList,on_delete=models.CASCADE,related_name='items')
    order=models.ForeignKey(Order,on_delete=models.PROTECT,related_name='pick_items')
    product=models.ForeignKey(Product,on_delete=models.PROTECT,related_name='pick_items')
    source_bin=models.ForeignKey(WarehouseBin,on_delete=models.SET_NULL,null=True,blank=True,related_name='pick_items')
    requested_qty=models.DecimalField(max_digits=12,decimal_places=2)
    picked_qty=models.DecimalField(max_digits=12,decimal_places=2,default=0)

class CycleCount(models.Model):
    class Status(models.TextChoices): OPEN='Open','Open'; COUNTED='Counted','Counted'; POSTED='Posted','Posted'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='cycle_counts')
    warehouse=models.ForeignKey(Warehouse,on_delete=models.PROTECT,related_name='cycle_counts')
    bin=models.ForeignKey(WarehouseBin,on_delete=models.PROTECT,related_name='cycle_counts')
    product=models.ForeignKey(Product,on_delete=models.PROTECT,related_name='cycle_counts')
    expected_qty=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    counted_qty=models.DecimalField(max_digits=12,decimal_places=2,null=True,blank=True)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.OPEN)
    counted_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

# --- Growth v3 / Phase 13: supplier portal ---
class SupplierPortalAccess(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='supplier_portal_access')
    supplier=models.OneToOneField(Supplier,on_delete=models.CASCADE,related_name='portal_access')
    email=models.EmailField()
    pin_hash=models.CharField(max_length=180)
    is_active=models.BooleanField(default=True)
    last_login_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['company','email'],name='unique_company_supplier_portal_email')]

class SupplierPortalSubmission(models.Model):
    class Type(models.TextChoices): PO_CONFIRM='PO_CONFIRM','PO confirmation'; ETA='ETA','Delivery ETA'; INVOICE='INVOICE','Invoice upload'; NOTE='NOTE','Note'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='supplier_portal_submissions')
    supplier=models.ForeignKey(Supplier,on_delete=models.PROTECT,related_name='portal_submissions')
    purchase_order=models.ForeignKey(PurchaseOrder,on_delete=models.SET_NULL,null=True,blank=True,related_name='supplier_submissions')
    submission_type=models.CharField(max_length=20,choices=Type.choices)
    payload=models.JSONField(default=dict,blank=True)
    status=models.CharField(max_length=30,default='Submitted')
    created_at=models.DateTimeField(auto_now_add=True)

# --- Growth v3 / Phase 14: workflow automation engine ---
class AutomationRule(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='automation_rules')
    name=models.CharField(max_length=140)
    event=models.CharField(max_length=60)
    conditions=models.JSONField(default=dict,blank=True)
    actions=models.JSONField(default=list,blank=True)
    is_active=models.BooleanField(default=True)
    last_run_at=models.DateTimeField(null=True,blank=True)
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class AutomationRun(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='automation_runs')
    rule=models.ForeignKey(AutomationRule,on_delete=models.CASCADE,related_name='runs')
    event=models.CharField(max_length=60)
    entity_type=models.CharField(max_length=60,blank=True)
    entity_id=models.CharField(max_length=80,blank=True)
    status=models.CharField(max_length=30,default='Completed')
    actions_executed=models.JSONField(default=list,blank=True)
    error=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

# --- Growth v3 / Phase 15: external commerce channel integration ---
class ExternalChannel(models.Model):
    class Provider(models.TextChoices): WEBSITE='WEBSITE','Website'; ONDC='ONDC','ONDC'; MARKETPLACE='MARKETPLACE','Marketplace'; CUSTOM='CUSTOM','Custom API'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='external_channels')
    name=models.CharField(max_length=120)
    provider=models.CharField(max_length=30,choices=Provider.choices,default=Provider.WEBSITE)
    external_store_id=models.CharField(max_length=120,blank=True)
    is_active=models.BooleanField(default=True)
    settings=models.JSONField(default=dict,blank=True)
    last_sync_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class ExternalOrder(models.Model):
    class Status(models.TextChoices): NEW='New','New'; REVIEW='Review','Review'; CONVERTED='Converted','Converted'; REJECTED='Rejected','Rejected'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='external_orders')
    channel=models.ForeignKey(ExternalChannel,on_delete=models.PROTECT,related_name='orders')
    external_id=models.CharField(max_length=120)
    customer_name=models.CharField(max_length=160)
    customer_phone=models.CharField(max_length=20,blank=True)
    ship_to=models.JSONField(default=dict,blank=True)
    total=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.NEW)
    raw_payload=models.JSONField(default=dict,blank=True)
    converted_order=models.ForeignKey(Order,on_delete=models.SET_NULL,null=True,blank=True,related_name='external_sources')
    received_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['channel','external_id'],name='unique_channel_external_order')]

class ExternalOrderItem(models.Model):
    external_order=models.ForeignKey(ExternalOrder,on_delete=models.CASCADE,related_name='items')
    external_sku=models.CharField(max_length=80)
    product=models.ForeignKey(Product,on_delete=models.SET_NULL,null=True,blank=True,related_name='external_order_items')
    name=models.CharField(max_length=180)
    quantity=models.DecimalField(max_digits=12,decimal_places=2)
    unit_price=models.DecimalField(max_digits=12,decimal_places=2)

# --- Growth v3 / Phase 16: manufacturer-distributor network visibility ---
class DistributionNetwork(models.Model):
    owner_company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='owned_distribution_networks')
    name=models.CharField(max_length=160)
    code=models.CharField(max_length=40,unique=True)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)

class NetworkMember(models.Model):
    network=models.ForeignKey(DistributionNetwork,on_delete=models.CASCADE,related_name='members')
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='network_memberships')
    region=models.CharField(max_length=100,blank=True)
    territory=models.CharField(max_length=100,blank=True)
    share_inventory=models.BooleanField(default=True)
    share_secondary_sales=models.BooleanField(default=True)
    is_active=models.BooleanField(default=True)
    joined_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['network','company'],name='unique_network_company_member')]

class NetworkSnapshot(models.Model):
    network=models.ForeignKey(DistributionNetwork,on_delete=models.CASCADE,related_name='snapshots')
    member=models.ForeignKey(NetworkMember,on_delete=models.CASCADE,related_name='snapshots')
    snapshot_date=models.DateField()
    inventory_value=models.DecimalField(max_digits=16,decimal_places=2,default=0)
    stock_units=models.DecimalField(max_digits=16,decimal_places=2,default=0)
    secondary_sales=models.DecimalField(max_digits=16,decimal_places=2,default=0)
    open_orders=models.PositiveIntegerField(default=0)
    product_summary=models.JSONField(default=list,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['network','member','snapshot_date'],name='unique_network_member_snapshot')]

# Phase 11 supporting collection assets
class PaymentLink(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='payment_links')
    customer=models.ForeignKey(Customer,on_delete=models.PROTECT,related_name='payment_links')
    invoice=models.ForeignKey(Invoice,on_delete=models.SET_NULL,null=True,blank=True,related_name='payment_links')
    token=models.CharField(max_length=80,unique=True)
    amount=models.DecimalField(max_digits=14,decimal_places=2)
    status=models.CharField(max_length=20,default='Active')
    expires_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class CollectionReminder(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='collection_reminders')
    customer=models.ForeignKey(Customer,on_delete=models.PROTECT,related_name='collection_reminders')
    invoice=models.ForeignKey(Invoice,on_delete=models.SET_NULL,null=True,blank=True,related_name='collection_reminders')
    channel=models.CharField(max_length=20,default='WhatsApp')
    scheduled_for=models.DateTimeField()
    status=models.CharField(max_length=20,default='Scheduled')
    message=models.CharField(max_length=500)
    created_at=models.DateTimeField(auto_now_add=True)

class ReceivableFinanceExport(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='receivable_finance_exports')
    export_no=models.CharField(max_length=40,unique=True)
    provider=models.CharField(max_length=40,default='TReDS-ready CSV')
    invoice_count=models.PositiveIntegerField(default=0)
    total_amount=models.DecimalField(max_digits=16,decimal_places=2,default=0)
    payload=models.JSONField(default=list,blank=True)
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

# Growth v3 WMS completion: wave picking and packing
class PickWave(models.Model):
    class Status(models.TextChoices):
        PLANNED='Planned','Planned'; RELEASED='Released','Released'; IN_PROGRESS='In Progress','In Progress'; COMPLETE='Complete','Complete'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='pick_waves')
    warehouse=models.ForeignKey(Warehouse,on_delete=models.PROTECT,related_name='pick_waves')
    wave_no=models.CharField(max_length=40,unique=True)
    pick_lists=models.ManyToManyField(PickList,related_name='waves',blank=True)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.PLANNED)
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class PackingSlip(models.Model):
    class Status(models.TextChoices):
        OPEN='Open','Open'; PACKED='Packed','Packed'; LABELLED='Labelled','Labelled'; DISPATCHED='Dispatched','Dispatched'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='packing_slips')
    warehouse=models.ForeignKey(Warehouse,on_delete=models.PROTECT,related_name='packing_slips')
    order=models.ForeignKey(Order,on_delete=models.PROTECT,related_name='packing_slips')
    pick_list=models.ForeignKey(PickList,on_delete=models.SET_NULL,null=True,blank=True,related_name='packing_slips')
    package_no=models.CharField(max_length=50,unique=True)
    carton_count=models.PositiveIntegerField(default=1)
    weight_kg=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.OPEN)
    packed_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    packed_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

# --- Growth v4 / Phase 17: CRM + sales pipeline ---
class CRMLead(models.Model):
    class Status(models.TextChoices):
        NEW='New','New'; QUALIFIED='Qualified','Qualified'; MEETING='Meeting','Meeting'; QUOTED='Quoted','Quoted'; NEGOTIATION='Negotiation','Negotiation'; WON='Won','Won'; LOST='Lost','Lost'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='crm_leads')
    lead_no=models.CharField(max_length=40,unique=True)
    name=models.CharField(max_length=160)
    business_name=models.CharField(max_length=180,blank=True)
    phone=models.CharField(max_length=20,blank=True)
    email=models.EmailField(blank=True)
    source=models.CharField(max_length=80,default='Referral')
    territory=models.CharField(max_length=100,blank=True)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.NEW)
    estimated_value=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    expected_close=models.DateField(null=True,blank=True)
    owner=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='crm_leads')
    lost_reason=models.CharField(max_length=240,blank=True)
    converted_customer=models.ForeignKey(Customer,on_delete=models.SET_NULL,null=True,blank=True,related_name='source_leads')
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)

class CRMActivity(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='crm_activities')
    lead=models.ForeignKey(CRMLead,on_delete=models.CASCADE,related_name='activities')
    activity_type=models.CharField(max_length=40,default='Call')
    note=models.CharField(max_length=300)
    next_follow_up=models.DateTimeField(null=True,blank=True)
    completed=models.BooleanField(default=False)
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

# --- Growth v4 / Phase 18: manufacturer schemes & claims ---
class ManufacturerScheme(models.Model):
    class SchemeType(models.TextChoices): REBATE='Rebate','Rebate'; TARGET='Target','Target'; FREE_QTY='Free Qty','Free Qty'; SLAB='Slab','Slab'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='manufacturer_schemes')
    supplier=models.ForeignKey(Supplier,on_delete=models.PROTECT,related_name='schemes')
    name=models.CharField(max_length=180)
    scheme_type=models.CharField(max_length=30,choices=SchemeType.choices,default=SchemeType.REBATE)
    start_date=models.DateField(); end_date=models.DateField()
    target_value=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    rebate_percent=models.DecimalField(max_digits=7,decimal_places=2,default=0)
    rules=models.JSONField(default=dict,blank=True)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)

class SchemeClaim(models.Model):
    class Status(models.TextChoices): ACCRUED='Accrued','Accrued'; SUBMITTED='Submitted','Submitted'; APPROVED='Approved','Approved'; REJECTED='Rejected','Rejected'; SETTLED='Settled','Settled'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='scheme_claims')
    scheme=models.ForeignKey(ManufacturerScheme,on_delete=models.PROTECT,related_name='claims')
    claim_no=models.CharField(max_length=40,unique=True)
    period_from=models.DateField(); period_to=models.DateField()
    eligible_value=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    claim_amount=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.ACCRUED)
    evidence=models.JSONField(default=list,blank=True)
    submitted_at=models.DateTimeField(null=True,blank=True); settled_at=models.DateTimeField(null=True,blank=True)

# --- Growth v4 / Phase 19: GST compliance cockpit ---
class GSTReconciliationItem(models.Model):
    class Status(models.TextChoices): MATCHED='Matched','Matched'; MISMATCH='Mismatch','Mismatch'; MISSING='Missing','Missing'; PENDING='Pending','Pending'; RESOLVED='Resolved','Resolved'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='gst_reconciliation_items')
    supplier=models.ForeignKey(Supplier,on_delete=models.SET_NULL,null=True,blank=True,related_name='gst_reconciliation_items')
    invoice_no=models.CharField(max_length=60)
    invoice_date=models.DateField(null=True,blank=True)
    gstin=models.CharField(max_length=20,blank=True)
    books_taxable=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    books_tax=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    portal_taxable=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    portal_tax=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    difference=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.PENDING)
    source=models.CharField(max_length=30,default='IMS')
    resolution_note=models.CharField(max_length=300,blank=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['company','invoice_no','source'],name='unique_company_gst_recon_invoice')]

# --- Growth v4 / Phase 20: smart procurement & vendor scorecards ---
class VendorScorecard(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='vendor_scorecards')
    supplier=models.OneToOneField(Supplier,on_delete=models.CASCADE,related_name='scorecard')
    price_score=models.DecimalField(max_digits=5,decimal_places=2,default=0)
    fill_rate=models.DecimalField(max_digits=5,decimal_places=2,default=0)
    on_time_rate=models.DecimalField(max_digits=5,decimal_places=2,default=0)
    quality_score=models.DecimalField(max_digits=5,decimal_places=2,default=0)
    payment_term_score=models.DecimalField(max_digits=5,decimal_places=2,default=0)
    overall_score=models.DecimalField(max_digits=5,decimal_places=2,default=0)
    avg_lead_days=models.DecimalField(max_digits=7,decimal_places=2,default=0)
    updated_at=models.DateTimeField(auto_now=True)

class ProcurementRecommendation(models.Model):
    class Status(models.TextChoices): OPEN='Open','Open'; APPROVED='Approved','Approved'; ORDERED='Ordered','Ordered'; DISMISSED='Dismissed','Dismissed'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='procurement_recommendations')
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='procurement_recommendations')
    supplier=models.ForeignKey(Supplier,on_delete=models.PROTECT,related_name='procurement_recommendations')
    recommended_qty=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    expected_unit_cost=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    expected_lead_days=models.PositiveIntegerField(default=0)
    reason=models.CharField(max_length=300,blank=True)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.OPEN)
    generated_at=models.DateTimeField(auto_now=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['company','product','supplier'],name='unique_procurement_product_supplier')]

# --- Growth v4 / Phase 21: fleet & route optimisation ---
class FleetVehicle(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='fleet_vehicles')
    vehicle_no=models.CharField(max_length=30)
    vehicle_type=models.CharField(max_length=60,default='LCV')
    capacity_kg=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    driver_name=models.CharField(max_length=120,blank=True)
    driver_phone=models.CharField(max_length=20,blank=True)
    cost_per_km=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    is_active=models.BooleanField(default=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['company','vehicle_no'],name='unique_company_fleet_vehicle')]

class RoutePlan(models.Model):
    class Status(models.TextChoices): PLANNED='Planned','Planned'; RELEASED='Released','Released'; RUNNING='Running','Running'; COMPLETE='Complete','Complete'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='route_plans')
    route_no=models.CharField(max_length=40,unique=True)
    vehicle=models.ForeignKey(FleetVehicle,on_delete=models.PROTECT,related_name='routes')
    warehouse=models.ForeignKey(Warehouse,on_delete=models.PROTECT,related_name='route_plans')
    route_date=models.DateField()
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.PLANNED)
    estimated_km=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    estimated_cost=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    optimization_score=models.DecimalField(max_digits=5,decimal_places=2,default=0)
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class RoutePlanStop(models.Model):
    route=models.ForeignKey(RoutePlan,on_delete=models.CASCADE,related_name='stops')
    order=models.ForeignKey(Order,on_delete=models.PROTECT,related_name='route_plan_stops')
    sequence=models.PositiveIntegerField(default=1)
    area=models.CharField(max_length=120,blank=True)
    delivery_window=models.CharField(max_length=60,blank=True)
    estimated_km_from_previous=models.DecimalField(max_digits=9,decimal_places=2,default=0)
    estimated_minutes=models.PositiveIntegerField(default=0)
    priority=models.PositiveSmallIntegerField(default=3)
    class Meta: ordering=['sequence']

# --- Growth v4 / Phase 22: credit scoring & embedded finance ---
class CustomerCreditScore(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='credit_scores')
    customer=models.OneToOneField(Customer,on_delete=models.CASCADE,related_name='credit_score')
    score=models.PositiveSmallIntegerField(default=50)
    risk_band=models.CharField(max_length=20,default='Medium')
    avg_payment_delay_days=models.DecimalField(max_digits=7,decimal_places=2,default=0)
    overdue_90=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    utilisation_percent=models.DecimalField(max_digits=7,decimal_places=2,default=0)
    suggested_limit=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    factors=models.JSONField(default=dict,blank=True)
    calculated_at=models.DateTimeField(auto_now=True)

class FinanceApplication(models.Model):
    class Status(models.TextChoices): DRAFT='Draft','Draft'; READY='Ready','Ready'; SUBMITTED='Submitted','Submitted'; APPROVED='Approved','Approved'; DECLINED='Declined','Declined'; FUNDED='Funded','Funded'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='finance_applications')
    customer=models.ForeignKey(Customer,on_delete=models.PROTECT,related_name='finance_applications',null=True,blank=True)
    application_no=models.CharField(max_length=40,unique=True)
    finance_type=models.CharField(max_length=40,default='Receivable Finance')
    requested_amount=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.DRAFT)
    provider=models.CharField(max_length=100,blank=True)
    payload=models.JSONField(default=dict,blank=True)
    created_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)

# --- Growth v4 / Phase 23: enterprise security & privacy administration ---
class UserMFASetting(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='mfa_setting')
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='mfa_settings')
    method=models.CharField(max_length=20,default='TOTP')
    secret_hash=models.CharField(max_length=128,blank=True)
    is_enabled=models.BooleanField(default=False)
    recovery_codes_hash=models.JSONField(default=list,blank=True)
    enabled_at=models.DateTimeField(null=True,blank=True)

class TrustedDevice(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='trusted_devices')
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='trusted_devices')
    device_id=models.CharField(max_length=100)
    device_name=models.CharField(max_length=160,blank=True)
    fingerprint_hash=models.CharField(max_length=128,blank=True)
    last_ip=models.GenericIPAddressField(null=True,blank=True)
    trusted=models.BooleanField(default=False)
    last_seen_at=models.DateTimeField(auto_now=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['company','user','device_id'],name='unique_company_user_device')]

class SecurityEvent(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='security_events')
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='security_events')
    event_type=models.CharField(max_length=80)
    severity=models.CharField(max_length=20,default='Info')
    ip_address=models.GenericIPAddressField(null=True,blank=True)
    device_id=models.CharField(max_length=100,blank=True)
    detail=models.JSONField(default=dict,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)

class PrivacyRequest(models.Model):
    class RequestType(models.TextChoices): ACCESS='Access','Access'; EXPORT='Export','Export'; CORRECT='Correct','Correct'; DELETE='Delete','Delete'; WITHDRAW='Withdraw Consent','Withdraw Consent'
    class Status(models.TextChoices): OPEN='Open','Open'; VERIFYING='Verifying','Verifying'; PROCESSING='Processing','Processing'; COMPLETE='Complete','Complete'; REJECTED='Rejected','Rejected'
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='privacy_requests')
    request_no=models.CharField(max_length=40,unique=True)
    subject_name=models.CharField(max_length=160)
    subject_email=models.EmailField(blank=True)
    request_type=models.CharField(max_length=30,choices=RequestType.choices)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.OPEN)
    due_date=models.DateField(null=True,blank=True)
    note=models.CharField(max_length=300,blank=True)
    created_at=models.DateTimeField(auto_now_add=True); completed_at=models.DateTimeField(null=True,blank=True)

class ConsentRecord(models.Model):
    company=models.ForeignKey(Company,on_delete=models.CASCADE,related_name='consent_records')
    subject_key=models.CharField(max_length=160)
    purpose=models.CharField(max_length=180)
    granted=models.BooleanField(default=True)
    source=models.CharField(max_length=80,default='Portal')
    captured_at=models.DateTimeField(auto_now_add=True)
    withdrawn_at=models.DateTimeField(null=True,blank=True)
