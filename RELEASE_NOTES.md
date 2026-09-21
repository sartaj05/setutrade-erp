# SetuStock NCR - Client Deployment Baseline

This release upgrades the earlier demo-focused repository into a production-oriented v1 baseline while preserving the safe frontend demo mode.

## Completed production baseline

- Multi-company hierarchy: Company -> Branch -> Warehouse -> User
- Tenant-scoped catalogue identifiers and company-isolated API queries
- Owner, Manager, Sales, Warehouse and Accountant access rules
- Server-backed access/refresh sessions, logout revocation, password change/reset and login throttling
- Product/customer CRUD foundation and CSV import/export
- Sales orders with line items, discounts, GST calculations, stock reservation and dispatch movements
- Quotations with conversion into sales orders
- GST invoice creation, ledger posting and printable invoice view
- Customer receipts and supplier payments
- Suppliers, purchase orders, approval gate and GRN inventory receipt
- Multi-warehouse balances and transfer approval/dispatch/receipt
- Barcode lookup, printable label workflow and browser camera support where BarcodeDetector is available
- WhatsApp draft parsing plus an optional server-side Meta Business Platform adapter
- Customer-specific pricing/quantity rules
- Sales/purchase returns and stock adjustments
- Field-sales visits, collections and targets
- Reorder suggestions and management reporting
- Company onboarding, branch creation, team accounts and client branding
- Global search, notifications, audit history and file attachments
- React PWA shell with strict production/demo separation
- PostgreSQL-ready settings, Dockerfiles, Docker Compose, health checks, backup/restore scripts and GitHub Actions CI

## Credentials/services intentionally not embedded

A source ZIP must never contain live vendor secrets. The following integrations are adapter/configuration ready but require the client's own credentials or provider selection before go-live:

- Meta WhatsApp Business Platform phone-number/token/template/webhook configuration
- SMTP transactional email provider
- Authorised GST e-invoice/e-way-bill provider
- Cloud object storage if media should not use a persistent server volume
- External error monitoring/APM provider

## Verification note

Python source compilation, shell-script syntax and Git whitespace/conflict checks were run in the packaging environment. The packaging environment cannot reach PyPI or npm, so a clean dependency installation and runtime test/build could not be executed locally. `.github/workflows/ci.yml` performs Django checks/migrations/tests and the React production build on GitHub runners.

Before using real client data, require a green CI run and complete the UAT checklist in `CLIENT_HANDOFF.md`.

## Growth v2 phases

This release adds the B2B customer portal, delivery/e-POD, approval workflows, purchase invoice OCR review, accounting exports, offline/PWA sync, SaaS subscription billing, advanced demand forecasting, a data-grounded business assistant, and an Expo-based Android/iOS client.

## Growth v3 expansion

Growth v3 adds phases 11–16: collections and reconciliation, advanced WMS, supplier collaboration, workflow automation, external sales-channel ingestion, and distributor-network visibility. It also includes public payment-link/UPI intent pages, WMS waves/packing, supplier demo authentication, mobile collection/WMS queues, additional seed data and API tests.

Provider boundaries remain explicit: generic ONDC/marketplace adapters are not a substitute for protocol certification; payment links do not confirm funds without a bank/payment provider callback; WhatsApp reminders require Meta/provider credentials; financing exports do not submit to a TReDS platform by themselves.

## Growth v4 — Phases 17–26

Added CRM pipeline, manufacturer scheme claims, GST reconciliation, smart procurement/vendor scorecards, fleet route planning, explainable customer credit risk, enterprise security/privacy administration, integration hub/public API, contribution-profit BI and approval-gated AI operational actions.

Security-sensitive additions store API keys and MFA setup material as hashes after enrollment; raw API/webhook setup secrets are returned only at creation time. The copilot requires human approval for transactional actions and logs executions.
