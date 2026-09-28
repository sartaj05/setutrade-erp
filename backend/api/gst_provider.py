import json
import os
import urllib.error
import urllib.request


class GSTProviderError(Exception):
    pass


def _invoice_payload(invoice):
    return {
        'invoiceNo': invoice.invoice_no,
        'invoiceDate': invoice.invoice_date.isoformat(),
        'sellerGstin': invoice.company.gstin,
        'buyerGstin': invoice.order.customer.gstin,
        'placeOfSupply': invoice.place_of_supply,
        'supplyType': invoice.supply_type,
        'taxableAmount': float(invoice.taxable_amount),
        'cgst': float(invoice.cgst),
        'sgst': float(invoice.sgst),
        'igst': float(invoice.igst),
        'total': float(invoice.total),
    }


def call_provider(action, invoice, extra=None):
    base_url = os.getenv('GST_PROVIDER_API_URL', '').rstrip('/')
    api_key = os.getenv('GST_PROVIDER_API_KEY', '')
    if not base_url or not api_key:
        raise GSTProviderError('GST provider credentials are not configured.')
    payload = {'action': action, 'invoice': _invoice_payload(invoice), **(extra or {})}
    request = urllib.request.Request(
        f'{base_url}/{action}',
        data=json.dumps(payload).encode(),
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            result = json.loads(response.read().decode() or '{}')
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        raise GSTProviderError(f'GST provider request failed: {exc}') from exc
    return result
