# SetuStock NCR Enhancement Suite

The demo now includes ten distribution-focused enhancements on top of the original inventory, customer, order and GST-invoice starter.

## 1. Suppliers, purchases and GRN
- Supplier master and payable context
- Purchase orders and expected dates
- Purchase line items and received quantity
- Goods receipt records
- React purchase pipeline + Django endpoints

## 2. Customer credit ledger and collections
- Invoice/payment/credit-note/adjustment ledger entries
- Due dates and ageing buckets
- Receivable and overdue dashboard
- Collection-ready customer view

## 3. Multi-warehouse inventory
- Warehouse master
- Product balance and reserved stock per warehouse
- Stock transfer headers/items
- In-transit/received transfer states

## 4. Barcode and QR workflow
- Product barcode and QR fields
- Scan log model
- Barcode/SKU lookup API
- USB-scanner-friendly React input and label workflow

## 5. WhatsApp B2B ordering
- Inbound/outbound WhatsApp message records
- WhatsApp draft-order model
- Message-to-product parsing example
- Draft order preview, stock context and quotation hand-off UI

The repository does not ship Meta credentials. Production WhatsApp Business Platform credentials, approved templates and webhooks must be configured by the deployer.

## 6. Advanced GST and tax notes
- Product HSN code and GST rate
- Place of supply and intra/inter-state invoice context
- CGST/SGST/IGST presentation
- Credit/debit notes
- Provider-ready e-invoice/e-way-bill status fields

No government or GST-provider credentials are embedded in the demo.

## 7. Customer-specific pricing and schemes
- Price lists
- Customer-specific lists
- Quantity break rules
- Discount and scheme text
- Interactive quantity-to-rate simulator

## 8. Returns, damaged stock and adjustments
- Sales/purchase returns
- Return line items and condition
- Damaged/count/expiry/other adjustments
- Return register and stock-adjustment audit-style UI

## 9. Field sales
- Sales visit plan and visit outcome
- Territory, customer, order value and collections
- Monthly sales and collection targets
- Mobile-friendly target progress view

## 10. Smart reorder and business intelligence
- Reorder suggestion model per SKU/warehouse
- Daily-sales rate, lead time, days of cover and risk
- Suggested replenishment quantity
- Receivable concentration and working-capital view

## Demo-mode architecture
Every enhanced React screen has bundled demo data. `useApiData` tries Django when the authenticated session is in API mode and falls back to demo data if the API request is unavailable. This lets the frontend be deployed by itself for sales demonstrations.
