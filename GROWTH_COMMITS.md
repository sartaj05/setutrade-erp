# Growth v2 feature-wise Git commits

The requested phases are intentionally separated so each feature can be reviewed, reverted, cherry-picked or demonstrated independently.

```text
a738c71  Phase 1   feat(portal): add B2B customer ordering portal
b3e0f4b  Phase 2   feat(delivery): add dispatch runs and electronic proof of delivery
a297522  Phase 3   feat(approvals): add policy-driven transaction approval workflows
b5347bc  Phase 4   feat(ocr): add supplier purchase invoice extraction and review
2c7d639  Phase 5   feat(accounting): add voucher exports and accounting connector layer
8bf103b  Phase 6   feat(offline): add PWA queue and idempotent field sync
9d57e8a  Phase 7   feat(billing): add SaaS plans subscriptions and client invoices
5ddbb68  Phase 8   feat(forecasting): add transparent demand and purchase planning
7950f01  Phase 9   feat(assistant): add data-grounded business question assistant
48ea7e9  Phase 10  feat(mobile): add Expo Android and iOS field operations client
0f3507a  QA        test(release): seed and validate growth v2 modules
```

After extracting the ZIP:

```bash
git log --oneline --reverse
git show a738c71
git show 48ea7e9
```
