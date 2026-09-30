# SetuStock public API and webhooks

The public order intake endpoint is available at `POST /api/public/v1/order-intake/`.
Send a scoped developer key in `X-SetuStock-Key`. Keys are created from the Integrations module and are shown only once.

Example payload:

```json
{
  "externalId": "shop-10042",
  "customerName": "Metro Electricals",
  "phone": "919999999999",
  "total": 6496
}
```

Use the Integrations module to create webhook subscriptions, rotate access by revoking a key, disable a subscription, and queue a failed delivery for retry. Delivery attempts and errors remain visible in the delivery log. A production delivery worker should sign each payload with the subscription secret and retry with exponential backoff before marking it failed.
