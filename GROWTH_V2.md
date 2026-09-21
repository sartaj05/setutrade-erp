# SetuStock Growth v2

This repository now contains all 10 requested growth phases on top of the production-baseline wholesale ERP.

| Phase | Feature | Main implementation |
|---|---|---|
| 1 | B2B Customer Portal | Separate `/portal` React experience, portal PIN auth, negotiated catalogue, credit view, cart and order requests |
| 2 | Delivery + Dispatch + e-POD | Delivery runs/stops, COD, status, OTP/signature/photo proof model |
| 3 | Approval Workflows | Company policies, thresholds, approver roles, approve/reject audit trail |
| 4 | Purchase Invoice OCR | Extraction/review workbench with supplier matching and human validation gate |
| 5 | Accounting Integration | Sales/purchase/receipt/payment voucher packs and Tally/Zoho/CSV connector layer |
| 6 | Offline Sales/PWA | Service-worker shell, IndexedDB web queue, idempotent Django sync endpoint |
| 7 | SaaS Subscription Billing | Plans, limits, trial/active state and subscription invoices |
| 8 | Advanced Forecasting | Recent-demand trend, safety stock, horizon forecast and recommended purchase quantity |
| 9 | AI Business Assistant | Tenant-scoped natural-language queries for sales, collections, receivables, stock and forecasts |
| 10 | Android/iOS App | Expo React Native client for field sales, orders, customers, delivery, assistant and offline sync |

## Demo credentials

Staff accounts remain `owner@setustock.demo`, `manager@setustock.demo`, `sales@setustock.demo`, `warehouse@setustock.demo`, and `accountant@setustock.demo`, each with password `demo123` after `python manage.py seed_demo`.

The B2B customer portal demo is `dealer@setustock.demo` with PIN `1234`.

## Production boundaries

OCR extraction included here is deterministic text extraction plus a provider-ready boundary. For scanned PDFs/photos in production, connect a dedicated OCR/document-AI provider and keep the existing human review step.

Accounting integration includes normalized voucher generation. Live Tally/Zoho authentication, tenant credentials and provider-specific webhooks must be configured per deployment.

SaaS billing models plan state and invoices; live card/UPI recurring payments require your chosen payment provider and webhook verification.

The assistant is data-grounded and useful without an external LLM. A hosted language-model provider can be added later behind the same endpoint, but tenant authorization and computed financial facts should remain server-side.
