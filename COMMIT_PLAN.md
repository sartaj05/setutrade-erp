# Feature-wise commit strategy

The repository already contains feature-scoped commits. Inspect them with:

```bash
git log --oneline --reverse
```

Current milestones:
1. Project brief and architecture
2. Landing page + trust-first light visual system
3. Login + role-based navigation
4. Role-aware dashboard
5. Inventory, customers, B2B orders and finance screens
6. Core Django APIs + signed authentication
7. Django-first / demo-fallback React integration
8. GST invoice module
9. Deployment configuration and verification

Recommended next commits for real product development:

```text
feat(tenancy): add organisation and branch isolation
feat(products): add product CRUD and validation
feat(stock): add stock movement ledger and adjustments
feat(purchases): add suppliers and purchase orders
feat(orders): add line items and stock reservation
feat(invoices): add GST calculation and PDF rendering
feat(credit): add customer ledger and ageing buckets
feat(payments): add receipt allocation and reconciliation
feat(whatsapp): add template messages and webhook delivery status
feat(audit): add immutable operational audit log
feat(reports): add sales margin stock and receivable exports
feat(testing): add API and React integration coverage
chore(ci): add build test and deployment pipeline
```
