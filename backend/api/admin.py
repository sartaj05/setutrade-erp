from django.contrib import admin
from .models import (
    BarcodeScanLog, Customer, GoodsReceipt, Invoice, LedgerEntry, Order, PriceList, PriceRule,
    Product, Profile, PurchaseItem, PurchaseOrder, ReorderSuggestion, ReturnItem, ReturnOrder,
    SalesTarget, SalesVisit, StockAdjustment, StockBalance, StockTransfer, StockTransferItem,
    Supplier, TaxNote, Warehouse, WhatsAppMessage, WhatsAppOrderDraft,
)

admin.site.register([
    Profile, Product, Customer, Order, Invoice, Supplier, PurchaseOrder, PurchaseItem, GoodsReceipt,
    LedgerEntry, Warehouse, StockBalance, StockTransfer, StockTransferItem, BarcodeScanLog,
    WhatsAppMessage, WhatsAppOrderDraft, TaxNote, PriceList, PriceRule, StockAdjustment, ReturnOrder,
    ReturnItem, SalesVisit, SalesTarget, ReorderSuggestion,
])
