from django.contrib import admin
from .models import (
    Attachment, AuditLog, Branch, Company, Customer, GoodsReceipt, InventoryMovement,
    Invoice, Notification, Order, OrderItem, Payment, Product, Profile, PurchaseOrder,
    Quotation, StockBalance, StockTransfer, Supplier, SupplierPayment, Warehouse,
)

for model in [
    Company, Branch, Profile, Product, Customer, Supplier, Warehouse, StockBalance,
    Order, OrderItem, Invoice, Quotation, PurchaseOrder, GoodsReceipt, Payment,
    SupplierPayment, StockTransfer, InventoryMovement, AuditLog, Notification, Attachment,
]:
    admin.site.register(model)
