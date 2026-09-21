# SetuStock production feature map

## Core business foundation

### Tenant and role isolation
- Company → Branch → Warehouse → User hierarchy
- Company-scoped operational queries
- Tenant-scoped product SKU/barcode, customer code, supplier code and warehouse code constraints
- Owner/Manager/Sales/Warehouse/Accountant permissions
- Read-only reference access where a role needs catalogues to perform its workflow

### Authentication and security
- Access + refresh signed sessions stored server-side
- Session revocation on logout/password reset
- Password change and password-reset flow
- Login throttling
- Production security headers/CORS controls
- Demo fallback disabled in production mode

## Sell-to-cash

### Customers and quotations
- Customer GST/contact/credit data
- Customer-specific prices and quantity slabs
- Quote creation and quote-to-order conversion

### Sales orders
- Order lines, GST calculation and discounts
- Warehouse assignment
- Confirm → reserve → pack → ready → dispatch flow
- Stock reservation and release
- Dispatch inventory movements

### GST invoices and collections
- CGST/SGST/IGST context
- HSN/GST rate lines
- Customer ledger posting
- Due dates and receivable ageing
- Customer receipts and payment methods
- Print-ready A4 invoice that can be saved as PDF
- Credit/debit notes
- Invoice attachments

## Procure-to-pay

### Suppliers and purchases
- Supplier master and outstanding balance
- Purchase order lines
- Approval gate
- GRN with partial receipt support
- Inventory increment on receipt
- Supplier ledger posting
- Supplier payments

## Inventory and fulfilment

### Warehouses
- Per-warehouse quantity/reserved balances
- Transfer request → approval → dispatch → receipt
- Inventory movements at source and destination

### Barcode / scanning
- Barcode/SKU lookup
- USB scanner/manual workflow
- Browser camera scanning where `BarcodeDetector` is supported
- Stock-in/stock-out actions
- Printable labels

### Returns and corrections
- Sales returns
- Purchase returns
- Damaged/expired/count/other adjustments
- Audit trail for inventory changes

## Sales channels and customer communication

### WhatsApp
- Inbound text-to-draft parser
- Outbound customer messages
- Optional Meta WhatsApp Business Platform adapter via backend credentials
- Credentials never shipped to React

### Field sales
- Customer visit plan/results
- Territory, order value and collections
- Monthly targets

## Management and operations

### Reports and intelligence
- Sales, purchases, collections, receivables, payables and stock value
- Reorder suggestions, days-of-cover and risk
- Top customer views
- CSV exports

### Administration
- Company onboarding and client branding
- Branch creation
- Team account creation/deactivation
- Global search
- Notifications
- Audit history
- File attachments
- Product/customer CSV import

## Deployment foundation
- React PWA shell
- Django WSGI/Gunicorn
- PostgreSQL-ready settings
- Dockerfiles + Docker Compose
- Static files through WhiteNoise
- Media volume support
- Database backup/restore scripts
- Health-check script
- GitHub Actions CI
- Transaction-flow API tests

## Integrations requiring client/vendor credentials
The repository deliberately does not contain third-party secrets. Production configuration is still required for:
- Meta WhatsApp Business Platform credentials and approved templates/webhooks
- SMTP/email provider for password reset
- Authorised GST/e-invoice/e-way-bill provider adapter
- Production object storage if files should not live on a server filesystem
- Error tracking/APM provider if desired

## Growth v3 commercial operations

### Collections command center
- Collection tasks and promise-to-pay tracking
- Payment transaction reconciliation and invoice allocations
- Partial/unapplied payment state
- Receipt/ledger posting
- Public payment links and UPI intent payloads
- Scheduled reminders and customer statements
- Receivable-financing export payloads

### Advanced WMS
- Warehouse bins/zones and bin stock
- Pick lists and source-bin suggestions
- Pick waves
- Packing slips
- Cycle counts and controlled variance posting
- Mobile WMS queue

### Supplier collaboration
- Separate supplier portal authentication
- Purchase-order visibility
- PO confirmation, ETA and invoice-reference submissions
- Staff supplier-response inbox

### Workflow automation
- Event/condition/action rules
- Notification, collection-task and reminder actions
- Execution history

### External commerce
- Website / ONDC / marketplace / custom channel registry
- Secret-key webhooks
- Idempotent external-order ingestion
- SKU matching and order conversion

### Distributor network
- Network ownership and membership
- Invitation/acceptance state
- Opt-in aggregate inventory and secondary-sales sharing
- Privacy-scoped member snapshots without customer-level exposure

## Growth v4 — commercial and enterprise intelligence

### CRM + sales pipeline
- Lead stages, ownership, follow-ups, expected close and pipeline conversion

### Manufacturer schemes and claims
- Rebate/target/slab scheme registry
- Accrual, claim submission and settlement tracking

### GST compliance cockpit
- Books vs IMS/provider reconciliation records
- Missing/mismatch queues and resolution notes

### Smart procurement
- Vendor performance scorecards
- Explainable purchase recommendations and approval status

### Fleet and route planning
- Fleet master, driver, capacity and per-km cost
- Route plans, sequenced stops and estimated route economics

### Credit risk and finance readiness
- Explainable customer credit scores and suggested limits
- Finance application workflow without representing lender approval

### Enterprise security and privacy operations
- MFA enrollment, device trust and security event history
- Consent and data-request workflows

### Integration hub and developer API
- Connector health, scoped hashed API keys and webhook subscriptions
- Public order-intake endpoint

### Executive BI
- Customer-level contribution profit and margin
- Period profitability snapshots

### AI action copilot
- Proposed operational actions with rationale and risk
- Human approval before execution
- Permission checks and audit logging
