# SetuStock feature-wise implementation plan

This file separates the next production work into six independent feature areas. Each area can be developed, tested, demonstrated, and released separately.

## 1. Production deployment and public API

Current foundation:

- Docker Compose runs PostgreSQL, Django/Gunicorn, and the React/Nginx frontend.
- `/api/health/` and `/api/ready/` are available for liveness and readiness checks.
- Production environment examples exist in `backend/.env.example` and `frontend/.env.example`.
- The frontend Docker build now accepts `VITE_API_URL` from the deployment environment.

Release checklist:

- Set `VITE_API_URL` to the public HTTPS API URL, or proxy `/api` through the same domain.
- Set `DJANGO_DEBUG=false`, a strong `DJANGO_SECRET_KEY`, explicit hosts, CORS, and CSRF origins.
- Use PostgreSQL, private object storage, SMTP, scheduled backups, monitoring, and HTTPS.
- Do not run `seed_demo` or use demo credentials in a client environment.

Acceptance test: a user on a different network can sign in, load `/api/ready/`, upload an attachment, and complete the order-to-payment workflow without any request going to their own `localhost`.

## 2. Real onboarding and data import

Current foundation:

- Company, branch, warehouse, team, CSV/XLSX preview, mapping, validation, duplicate review, commit, rollback, import history, and onboarding feedback.

Next production work:

- Add client-specific import templates and downloadable sample files.
- Require a validation report download before commit.
- Add opening supplier balances and invoice/payment opening balance reconciliation.
- Add an onboarding owner, due date, and checklist completion audit.

Acceptance test: a client can migrate approved master data, understand every rejected row, commit only after review, and restore the previous state with rollback.

## 3. Payments and bank reconciliation

Current foundation:

- Payment links, signed webhook handling, duplicate protection, invoice allocation, unapplied balances, and manual reconciliation.

Next production work:

- Select and implement the client’s payment/bank provider adapter.
- Validate provider signatures in staging and production.
- Import bank statements with a reviewable matching queue.
- Import bank CSV statements with customer matching, duplicate detection, debit filtering, and an unmatched review queue.
- Add settlement, refund, chargeback, failed-payment, and unmatched-payment states.
- Update invoice, order, customer ledger, and audit records atomically.

Acceptance test: a real or sandbox payment is received once, matched to the correct invoice, never duplicated on webhook replay, and remains visible when it cannot be matched automatically.

## 4. GST e-invoice and e-way bill

Current foundation:

- GST invoice data, tax notes, provider action boundary, IRN, QR payload, and e-way bill action placeholders.

Next production work:

- Choose an authorised IRP/GSP/ASP provider and implement its request/response adapter.
- Add signed request authentication, retry, idempotency, cancellation, and provider error mapping.
- Store IRN, signed QR payload, acknowledgement number, e-way bill number, and validity dates.
- Add Ship-to GSTIN/URP validation and reporting-deadline alerts.

Acceptance test: staff can generate, retry, cancel, download, and audit an e-invoice/e-way bill from a staging provider without changing the invoice twice.

## 5. WhatsApp inbox

Current foundation:

- Signed Meta webhook verification, inbound order drafts, outbound message records, payment reminders, and provider-ready delivery.

Next production work:

- Add a conversation inbox with assignment, unread state, status filters, and customer history.
- Configure approved Meta templates and opt-in/opt-out records.
- Store delivery, read, failure, and provider message IDs from webhook events.
- Add retry controls and human approval before order conversion or customer-facing sends.

Acceptance test: an inbound customer message appears in the correct company inbox, creates a reviewable order draft, and every outbound status is traceable to the provider message ID.

## 6. Accounting integration

Current foundation:

- Voucher-pack generation for sales, purchase, receipt, and payment records, connector configuration, and export history.

Next production work:

- Start with one provider selected by the client, such as Tally or Zoho Books.
- Add field mapping, tax-ledger mapping, sync cursor, retry queue, and conflict handling.
- Add export/download and import/reconciliation reports.
- Never post automatically until the accountant approves the first mapping and test batch.

Acceptance test: a test period can be exported, imported into the selected accounting system, reconciled back to SetuStock, and safely retried without duplicate vouchers.

## User feedback form

Ask every pilot user these questions after attempting a real workflow:

1. Which workflow did you try first?
2. Where did you get stuck?
3. Which task still requires Excel, WhatsApp, paper, or another app?
4. Do you trust the payment, GST, stock, and outstanding figures? Why or why not?
5. What must work offline on mobile?
6. Which report or notification do you need every day?

Use the answers to prioritize integration reliability before adding more dashboard screens.
