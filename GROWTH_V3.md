# SetuStock Growth v3

Growth v3 adds the next commercial layer on top of the Growth v2 wholesale/distribution platform.

## Phase 11 — Collections & reconciliation

- Payment transaction feed and automatic allocation to oldest open invoices
- Partial/unapplied payment handling
- Customer promise-to-pay records and collection tasks
- Public payment links with UPI intent payloads
- Scheduled collection reminders
- Customer statement API and receipt creation
- Receivable-financing/TReDS-ready export payload
- Mobile collection work queue

Live UPI/payment confirmation, WhatsApp sending and financing submission still require the client's chosen providers and credentials.

## Phase 12 — Advanced WMS

- Warehouse zones/bins and per-bin stock
- Pick lists and source-bin suggestions
- Pick waves for grouped warehouse work
- Packing slips/carton/weight capture
- Cycle counting and controlled stock variance posting
- Mobile WMS queues

## Phase 13 — Supplier portal

- Separate supplier sign-in surface
- Supplier-specific purchase orders
- PO confirmation responses
- Delivery ETA updates
- Invoice metadata/file-reference submissions
- Internal supplier-response inbox

Demo supplier login: `supplier@setustock.demo` / `1234`.

## Phase 14 — Workflow automation

- Event + condition + action rules
- Numeric threshold operators
- Notification actions
- Collection-task actions
- Collection-reminder scheduling
- Rule execution history

Production event triggering can be connected to background jobs/webhooks; the built-in test runner executes rules synchronously.

## Phase 15 — External sales channels

- Channel registry for Website / ONDC / Marketplace / Custom adapters
- Idempotent external-order ingestion
- SKU matching against SetuStock products
- Review queue and ERP order conversion
- Secret-key webhook endpoint per channel

The `ONDC` provider type is an adapter boundary, not a complete ONDC protocol certification. A real seller-app/network integration must implement the currently required ONDC protocol, signing, callbacks and compliance outside the generic ingestion boundary.

## Phase 16 — Distributor network

- Manufacturer/distributor network records
- Member invitation/acceptance state
- Opt-in inventory sharing
- Opt-in secondary-sales sharing
- Aggregate network snapshots
- Product-level stock summary without customer-level visibility

The design intentionally shares aggregate operational data rather than customer records.

## Public/demo routes

- `/login` — staff ERP
- `/portal` — dealer/customer B2B portal
- `/supplier-portal` — supplier workspace
- `/pay/demo-rk-payment-link` — payment-link demo after `seed_demo`

## Migration range

Growth v3 uses migrations `0025` through `0032`.
