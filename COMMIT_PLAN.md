# Feature-wise Git history

This repository is intentionally committed feature-by-feature. Inspect the actual history with:

```bash
git log --oneline --reverse
```

## Original foundation commits

1. `chore: bootstrap SetuStock NCR project brief`
2. `feat(frontend): add trust-first landing page and visual system`
3. `feat(auth): add demo login and role-based application shell`
4. `feat(dashboard): add role-aware operational overview`
5. `feat(operations): add inventory customer order and finance demo modules`
6. `feat(backend): add core Django auth inventory customer and order APIs`
7. `feat(integration): prefer Django API with automatic demo-data fallback`
8. `feat(invoices): add GST invoice demo and Django API support`
9. `chore(deploy): add demo deployment config environments and hardening notes`
10. `chore(frontend): align React and Vite toolchain with current releases`

## Ten enhancement commits

1. `feat(purchases): add suppliers purchase orders and goods receiving`
2. `feat(ledger): add customer credit ageing and collections`
3. `feat(warehouse): add multi-location inventory and stock transfers`
4. `feat(barcode): add product scanning and label workflow`
5. `feat(whatsapp): add B2B ordering and customer chat drafts`
6. `feat(gst): add advanced GST notes and e-invoice readiness`
7. `feat(pricing): add customer price lists and quantity schemes`
8. `feat(returns): add returns damage and stock adjustments`
9. `feat(sales): add field-sales visits targets and collections`
10. `feat(insights): add reorder intelligence and business analytics`

The final repository-quality commit adds CI, tests, updated documentation and validation fixes without squashing the feature history.

## Growth v4 phase commits

1. `feat(crm): add leads opportunities followups and sales pipeline`
2. `feat(schemes): add manufacturer incentives rebates and claims`
3. `feat(gst): add compliance cockpit and IMS reconciliation`
4. `feat(procurement): add vendor scoring and intelligent purchase planning`
5. `feat(logistics): add route planning fleet tracking and delivery optimisation`
6. `feat(credit): add trade credit scoring and financing readiness`
7. `feat(security): add MFA device controls and privacy administration`
8. `feat(integrations): add connector hub webhooks and public API`
9. `feat(analytics): add contribution margin and profitability intelligence`
10. `feat(copilot): add permission-gated AI operational actions`
