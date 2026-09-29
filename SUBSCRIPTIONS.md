# Subscription enforcement

SetuStock now enforces subscription access in both the Django API and the workspace navigation.

## Plans

- Free: core inventory, customers, quotations and orders; 3 users, 100 products, 1 branch, 1 warehouse and 100 orders per month.
- Premium: GST invoices, payments, WhatsApp, delivery, approvals, field sales, forecasting, assistant and operational automation; 10 users, 2,500 products, 3 branches, 5 warehouses and 1,000 orders per month.
- Enterprise: multi-branch administration, advanced reports, integrations, security, BI and AI actions; 50 users, 10,000 products, 20 branches, 50 warehouses and 10,000 orders per month.

## Enforcement behavior

- Authenticated API requests check the company subscription before protected module handlers run.
- Locked features return HTTP `402` with `error: subscription_required`, `requiredPlan`, `currentPlan` and an upgrade URL.
- Create and import operations enforce product, user, branch, warehouse and monthly order limits.
- Expired trials, past-due subscriptions and cancelled subscriptions retain core access but block paid features.
- Plan changes, cancellations, resumes and administrative plan-limit edits are written to the company audit log.
- `/api/auth/me/` and `/api/subscription/` expose plan status, expiry, limits, current usage and feature access for the frontend.

The frontend uses this same entitlement data to mark locked sidebar modules and guide the user to Subscription billing.
