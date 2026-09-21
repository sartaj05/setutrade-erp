# SetuStock Growth v5 — Phases 27–36

Growth v5 deepens SetuStock from broad distributor ERP coverage into master-data governance, physical traceability, finance control, contract operations, quality, planning, after-sales service, expense control, self-service reporting and production observability.

## Phase 27 — Product Master / PIM + Data Governance
- Governed product master profile linked to the existing Product record.
- Brand, manufacturer, UOM conversions, alternate barcodes, commercial prices, weight/dimensions and traceability flags.
- Preferred supplier, min/max/reorder controls and data-quality score.
- Product change request workflow with owner/manager/accountant approval.

## Phase 28 — Batch / Lot / Serial / Expiry Traceability
- Inventory lots by product and warehouse.
- Batch/manufacture/expiry dates and lot-level available quantity.
- Serial-unit registry with customer/order/warranty linkage.
- Traceability events and lot recall state.

## Phase 29 — Treasury + Bank Reconciliation + Cash Flow
- Multiple bank/cash accounts.
- Imported/manual bank statement transactions.
- Reference/amount reconciliation against collection transactions.
- Seven-day cash-flow forecast based on current balances, receivables and payables.

## Phase 30 — Contract Pricing + Rate Agreements + Tenders
- Customer rate agreements with validity and credit terms.
- Product-specific contract rates, quantity limits and escalation percentage.
- Tender opportunity register and expected value tracking.

## Phase 31 — Quality Control + Inspection
- Incoming/outgoing inspection records.
- Quantity inspected/passed/rejected/quarantined.
- JSON checklist for vertical-specific QC criteria.
- Quarantine stock release workflow.

## Phase 32 — Advanced Replenishment / S&OP
- Planning scenarios with horizon, demand multiplier and supplier-delay assumptions.
- Per-product replenishment recommendations.
- Inter-warehouse transfer quantity vs fresh purchase quantity.
- Approval state for recommended plans.

## Phase 33 — Warranty + RMA + After-Sales Service
- Service tickets linked to customers, products and serialized units.
- Warranty validity and technician/diagnosis workflow.
- RMA repair/replacement actions and manufacturer claim values.

## Phase 34 — Expense + Petty Cash + Employee Claims
- Employee expense submissions with branch/category/receipt metadata.
- Manager/accountant approval.
- Petty-cash accounts and posted payout transactions.

## Phase 35 — Custom Report Builder + Scheduled Reports
- Saved report definitions with data source, dimensions, measures, filters and grouping.
- Delivery schedules, recipients and output format.
- Report-run history for operational visibility.

## Phase 36 — Operations Control Center
- Internal/provider service-health registry with latency and status.
- Background job failure/retry queue.
- Failed webhook replay queue.
- Configurable alert policies.

## API endpoints

- `/api/product-master/`
- `/api/traceability/`
- `/api/treasury/`
- `/api/contracts/`
- `/api/quality/`
- `/api/supply-planning/`
- `/api/service-rma/`
- `/api/expenses/`
- `/api/report-builder/`
- `/api/operations-center/`

All new APIs are company-scoped and role-guarded.
