# SetuStock growth and product summary

This is the single source of truth for the product scope, completed growth phases, commercial packaging, and known provider boundaries. The repository contains the complete SetuStock wholesale and distribution platform through Growth v5 (phases 1-36).

## Product foundation

SetuStock is a multi-tenant B2B wholesale and distribution platform for Indian businesses. It brings inventory, purchasing, customer credit, quotations, orders, GST invoices, payments, delivery, WhatsApp workflows, reporting, and role-based operations into one system.

Primary roles:

- Owner: full visibility, settings, billing, security, and approvals
- Manager: sales, inventory, purchasing, approvals, and team operations
- Sales: customers, quotations, orders, collections, WhatsApp, and field visits
- Warehouse: products, stock, barcode, purchasing, fulfilment, and delivery
- Accountant: invoices, payments, ledgers, GST, reports, and reconciliation

Core platform capabilities include tenant-scoped Company -> Branch -> Warehouse -> User records, server-backed sessions, password reset, login throttling, role guards, audit logs, notifications, global search, attachments, CSV imports, a React PWA, a Django API, PostgreSQL support, Docker deployment, health/readiness checks, backup/restore scripts, and GitHub Actions CI.

## Growth phases

### Growth v2: phases 1-10

| Phase | Capability | Delivered scope |
| ---: | --- | --- |
| 1 | B2B customer portal | Dealer PIN login, negotiated catalogue, credit view, cart, and order requests |
| 2 | Delivery and e-POD | Delivery runs/stops, COD, status, OTP, signature, photo, and proof records |
| 3 | Approval workflows | Policy thresholds, approver roles, approval/rejection audit trail |
| 4 | Purchase invoice OCR | Deterministic extraction, supplier matching, and human review gate |
| 5 | Accounting integration | Sales/purchase/receipt/payment voucher packs and connector boundary |
| 6 | Offline sales/PWA | Service-worker shell, IndexedDB queue, and idempotent sync endpoint |
| 7 | SaaS subscriptions | Plans, usage limits, trials, subscription invoices, renewals, and payment retry state |
| 8 | Demand forecasting | Demand trend, safety stock, horizon forecast, and purchase recommendations |
| 9 | Business assistant | Tenant-scoped data-grounded questions for sales, collections, receivables, stock, and forecasts |
| 10 | Mobile client | Expo Android/iOS app for field sales, orders, customers, delivery, assistant, and offline sync |

### Growth v3: phases 11-16

- Collections and reconciliation: payment allocation, partial/unapplied payments, promises, collection tasks, public UPI payment links, reminders, statements, and financing-ready exports.
- Advanced WMS: zones, bins, bin stock, pick lists, waves, packing slips, cycle counts, controlled variance posting, and mobile queues.
- Supplier portal: supplier sign-in, purchase-order visibility, confirmation, ETA updates, invoice references, and staff response inbox.
- Workflow automation: event/condition/action rules, notifications, collection tasks, reminders, and execution history.
- External sales channels: Website/ONDC/marketplace/custom registry, idempotent ingestion, SKU matching, review queue, order conversion, and keyed webhooks.
- Distributor network: invitations, acceptance, opt-in aggregate inventory/secondary-sales sharing, and privacy-scoped member snapshots.

### Growth v4: phases 17-26

- CRM pipeline: leads, ownership, stages, activities, follow-ups, expected close, and conversion summaries.
- Manufacturer schemes and claims: targets, slabs, rebates, accruals, evidence, submission, approval, and settlement.
- GST compliance cockpit: books-versus-IMS/provider reconciliation, mismatch queues, tax exposure, and resolution notes.
- Smart procurement: vendor scorecards, low-stock recommendations, and buyer approval.
- Fleet and routes: vehicle/driver/capacity registry, sequenced stops, route economics, and optimisation score.
- Credit risk: explainable trade-credit score, suggested limits, risk bands, and finance application workflow.
- Security and privacy: MFA setup, trusted devices, security events, consent, and data-subject requests.
- Integration hub: connector health, hashed/scoped API keys, webhook subscriptions, delivery logs, and public order intake.
- Executive BI: contribution-profit snapshots, revenue, COGS, returns, discounts, and margin.
- AI action copilot: bounded proposals with rationale, risk, human approval, permission checks, and audit logging.

### Growth v5: phases 27-36

- Product Master/PIM and governed product changes
- Batch, lot, serial, expiry, recall, and traceability events
- Treasury, bank reconciliation, and seven-day cash-flow forecasting
- Customer rate agreements, contract pricing, and tenders
- Quality inspections, quarantine, and controlled release
- Advanced replenishment and S&OP scenarios with transfer-versus-purchase recommendations
- Warranty, RMA, technician workflow, and manufacturer recovery claims
- Employee expenses, petty cash, receipts, and approval workflow
- Custom report definitions, schedules, recipients, formats, and run history
- Operations control center with service health, job retries, webhook replay, and alert policies

Growth v5 API surfaces:

```text
/api/product-master/       /api/traceability/
/api/treasury/             /api/contracts/
/api/quality/              /api/supply-planning/
/api/service-rma/          /api/expenses/
/api/report-builder/       /api/operations-center/
```

All growth APIs are company-scoped and role-guarded. The frontend includes demo data for the growth modules, so the demo can run without Django when `VITE_APP_MODE=demo` and `VITE_DEMO_FALLBACK=true`.

## Subscription packaging

| Plan | Limits | Included scope |
| --- | --- | --- |
| Free | 3 users, 100 products, 1 branch, 1 warehouse, 100 monthly orders | Core inventory, customers, quotations, and orders |
| Premium | 10 users, 2,500 products, 3 branches, 5 warehouses, 1,000 monthly orders | GST, payments, WhatsApp, delivery, approvals, field sales, forecasting, assistant, WMS, procurement, quality, and service workflows |
| Enterprise | 50 users, 10,000 products, 20 branches, 50 warehouses, 10,000 monthly orders | Advanced reports, multi-branch administration, integrations, treasury, contracts, expenses, security, BI, AI actions, and operations control |

The API enforces plan access and usage limits. Locked features return HTTP 402 with the required plan and upgrade URL. Plan changes, cancellations, resumes, and limit edits are audit logged. The frontend reads the same entitlement payload to mark locked modules.

## Demo surfaces

- Staff ERP: `/login`
- Dealer portal: `/portal`, `dealer@setustock.demo` / `1234`
- Supplier portal: `/supplier-portal`, `supplier@setustock.demo` / `1234`
- Payment page: `/pay/demo-rk-payment-link`
- Staff demo accounts use password `demo123` after `python manage.py seed_demo`.

## Provider and compliance boundaries

The repository does not contain vendor secrets. Live payment confirmation, WhatsApp delivery, GST/e-invoice/e-way-bill submission, accounting synchronisation, OCR for scanned documents, maps/GPS, financing submission, ONDC certification, SMTP, object storage, and monitoring require client-owned credentials and provider-specific staging validation.

The generic ONDC/channel adapter normalizes orders but is not protocol certification. Payment links create intent payloads but do not prove funds without a bank/provider callback. AI features create approval-ready proposals; transactional or customer-facing actions require human approval. SetuStock is not itself a certified GST filing or accounting product.

## Feature history

Feature commits remain available in Git history and are intentionally not rewritten. Inspect them with:

```bash
git log --oneline --reverse
```

The phase commit ranges are Growth v2 (`a738c71` through `48ea7e9`), Growth v3 (`5e04b84` through `c7f41a3`), Growth v4 (`b641485` through `2a13098`), and Growth v5 (`8a1dec2` through `addef64`, with shared integration at `2272081`).
