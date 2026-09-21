# SetuStock Growth v4 — Phases 17–26

Growth v4 deepens SetuStock from an operational distributor ERP into a commercial, integration and enterprise-control platform.

## Phase 17 — CRM + Sales Pipeline
- Lead capture, source, territory, owner and expected close
- Stage progression from New → Qualified → Meeting → Quoted → Negotiation → Won/Lost
- Activities and follow-up dates
- Pipeline value and conversion summary

## Phase 18 — Manufacturer Schemes & Claims
- Manufacturer/supplier schemes, targets, slabs and rebate rates
- Accrued/submitted/approved/rejected/settled claims
- Evidence payloads and settlement state

## Phase 19 — GST Compliance Cockpit
- Books-vs-portal/IMS reconciliation records
- Matched, mismatch, missing and resolved states
- Tax difference exposure and resolution notes
- Provider data must be connected for live GST/IMS retrieval

## Phase 20 — Smart Procurement + Vendor Scorecards
- Supplier scorecards for price, fill rate, on-time delivery, quality and payment terms
- Low-stock purchase recommendations
- Buyer approval state before purchasing

## Phase 21 — Fleet & Route Optimisation
- Vehicle/driver/capacity/cost-per-km registry
- Route plans and ordered delivery stops
- Estimated route kilometres/cost and optimisation score
- Current optimizer is deterministic planning logic; live GPS/maps require a mapping provider

## Phase 22 — Credit Scoring + Finance Readiness
- Explainable trade-credit score based on outstanding, utilisation and overdue ledger exposure
- Suggested customer credit limit and risk band
- Finance application records for receivable/working-capital workflows
- No external lender decision is represented as a SetuStock decision

## Phase 23 — Enterprise Security + Privacy Administration
- MFA enrollment state and one-time setup material
- Trusted-device registry and security events
- Consent records and data-subject request workflow
- These are operational privacy/security controls, not legal certification

## Phase 24 — Integration Hub + Public API
- Connector registry and sync health
- Hashed, scoped developer API keys
- Webhook subscriptions and delivery log
- Public order-intake API using `X-SetuStock-Key`
- Raw API/webhook secrets are returned only at creation time

## Phase 25 — Executive BI + Profitability
- Customer contribution-profit snapshots
- Revenue, COGS, gross profit, discounts, returns and contribution margin
- Rebuildable period snapshots from ERP transactions
- Delivery/finance costs are explicit fields and can be populated by connected cost feeds

## Phase 26 — AI Action Copilot
- Converts plain-language requests into bounded action proposals
- Tenant-scoped data access
- Risk level and rationale stored with every proposal
- Owner/manager approval required before transactional execution
- Current executable actions: collection-task creation and procurement-recommendation approval
- Procurement approval does not send a supplier PO automatically
- Every approved execution is written to the audit log

## New API routes

```text
/api/crm/
/api/schemes/
/api/gst-cockpit/
/api/procurement-intelligence/
/api/fleet-routes/
/api/credit-risk/
/api/security-center/
/api/integrations/
/api/public/v1/order-intake/
/api/executive-bi/
/api/copilot-actions/
```

## Demo mode
All ten staff modules have bundled frontend data so the React client can be shared without a backend when `VITE_APP_MODE=demo` and `VITE_DEMO_FALLBACK=true`.

## Production boundaries
Live GST retrieval, payment/finance provider actions, route maps/GPS, WhatsApp, accounting systems and other vendor integrations still require client-owned credentials and provider-specific adapters. Secrets must be supplied through deployment configuration, not committed to Git.
