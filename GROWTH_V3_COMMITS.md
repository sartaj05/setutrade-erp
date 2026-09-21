# Growth v3 commit map

Growth v3 was added on top of the existing Growth v2 history. The repository remains on `main`.

## Phase feature commits

```text
5e04b84 feat(collections): add automated collections and payment reconciliation
06b49bf feat(wms): add bins pick lists and cycle counting
16bffb2 feat(supplier-portal): add PO confirmation ETA and invoice submission portal
ad2239a feat(automation): add event rules conditions and operational actions
51f366c feat(channels): add website ONDC and marketplace order ingestion layer
f56fdf9 feat(network): add privacy-scoped distributor network visibility
```

## Completion / client-surface commits

```text
ca13f23 feat(frontend): add growth v3 operational modules
58c7dc7 feat(collections): add payment links reminders statements and financing export
348864d feat(supplier-portal): add standalone supplier web workspace
08a5de7 fix(rbac): expose growth v3 modules by staff role
cc42b36 test(seed): add growth v3 demo records
57de931 feat(mobile): add field collections and WMS work queues
12a51ef test(growth-v3): cover collections WMS supplier portal channels and networks
eb61b55 fix(expansion): harden growth v3 APIs and channel webhooks
39704aa feat(wms): add waves packing count posting and reminder automation
486ad6b feat(payments): add public payment links and UPI intent page
ab304ab feat(frontend): surface WMS waves and packing
9ff8e8c test(seed): add WMS wave and packing demo data
2d139d5 feat(demo): expose dealer and supplier portal entry points
8aee3d9 docs(growth-v3): document phases provider boundaries and client demo
c7f41a3 ci(growth-v3): validate migrations seed data tests and builds
```

Run this for the entire project history:

```bash
git log --oneline --reverse
```
