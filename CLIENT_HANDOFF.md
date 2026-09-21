# Client handoff guide

## Best way to share the first demo

Use a frontend-only **demo deployment**. It is intentionally isolated from real customer information and continues to work without a Django host.

Build variables:

```env
VITE_APP_MODE=demo
VITE_DEMO_FALLBACK=true
VITE_API_URL=https://an-unavailable-demo-api.example/api
```

Share the URL together with one or two demo accounts instead of all roles at once. `owner@setustock.demo / demo123` is the broadest walkthrough account.

## Before accepting real client data

1. Deploy Django with PostgreSQL and a strong `DJANGO_SECRET_KEY`.
2. Set `DJANGO_DEBUG=false` and HTTPS-only settings.
3. Build React with `VITE_APP_MODE=production` and `VITE_DEMO_FALLBACK=false`.
4. Create the client's owner account and company/branch/warehouse records. Do not run public demo users on the live database.
5. Configure SMTP so password reset emails are delivered.
6. Configure automated PostgreSQL backups and test a restore.
7. Decide where uploaded documents are stored. For multi-server/cloud deployments, use object storage instead of local filesystem media.
8. Configure monitoring/error reporting and an uptime check against `/api/health/`.
9. Add Meta WhatsApp credentials only if the client has the required Business Platform setup.
10. Validate GST invoice/e-invoice/e-way-bill requirements with the client's accountant/compliance provider before enabling statutory integrations.

## Client acceptance walkthrough

Use this sequence during UAT:

1. Owner signs in and verifies company/GST/bank/settings.
2. Create a branch, warehouse, team user and roles.
3. Import/create products, customers and suppliers.
4. Create and approve a PO, receive it through GRN, confirm stock increases.
5. Create a quotation and convert it into a sales order.
6. Confirm the order and verify reserved stock.
7. Pack/ready/dispatch and verify stock decreases.
8. Create the GST invoice and verify customer ledger/outstanding.
9. Record a customer payment and verify receivable reduces.
10. Transfer stock between warehouses and verify both locations.
11. Process a return/adjustment and review the audit log.
12. Export reports and inspect notifications/search/attachments.

## Production ownership

Before go-live, replace demo branding and credentials, create a backup owner account, document who controls the domain/database/vendor credentials, and record the restore procedure. A ZIP on someone's Downloads folder is not, despite centuries of human optimism, a disaster-recovery plan.
