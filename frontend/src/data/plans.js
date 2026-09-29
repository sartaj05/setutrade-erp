export const PLAN_LEVELS = { FREE: 0, PREMIUM: 1, ENTERPRISE: 2 };

// Keep the public plan names stable while the API remains backwards compatible
// with its original STARTER / GROWTH / BUSINESS codes.
export function normalizePlan(code) {
  const value = String(code || 'FREE').toUpperCase();
  if (value === 'STARTER' || value === 'FREE') return 'FREE';
  if (value === 'GROWTH' || value === 'PREMIUM') return 'PREMIUM';
  if (value === 'BUSINESS' || value === 'ENTERPRISE') return 'ENTERPRISE';
  return 'FREE';
}

export const PLAN_LABELS = { FREE: 'Free', PREMIUM: 'Premium', ENTERPRISE: 'Enterprise' };

// A role can still hide a module. This table only decides whether the
// subscribed company can use a module that its role already exposes.
export const PLAN_REQUIREMENTS = {
  whatsapp: 'PREMIUM', tax: 'PREMIUM', approvals: 'PREMIUM', 'field-sales': 'PREMIUM',
  invoices: 'PREMIUM', payments: 'PREMIUM', delivery: 'PREMIUM', collections: 'PREMIUM',
  offline: 'PREMIUM', forecasting: 'PREMIUM', assistant: 'PREMIUM', traceability: 'PREMIUM',
  wms: 'PREMIUM', 'invoice-ocr': 'PREMIUM', accounting: 'PREMIUM', 'gst-cockpit': 'PREMIUM',
  'procurement-intelligence': 'PREMIUM', 'fleet-routes': 'PREMIUM', 'product-master': 'PREMIUM',
  'service-rma': 'PREMIUM', quality: 'PREMIUM', 'supply-planning': 'PREMIUM',
  'distribution-network': 'ENTERPRISE', 'credit-risk': 'ENTERPRISE', 'security-center': 'ENTERPRISE',
  integrations: 'ENTERPRISE', 'executive-bi': 'ENTERPRISE', 'copilot-actions': 'ENTERPRISE',
  treasury: 'ENTERPRISE', contracts: 'ENTERPRISE', expenses: 'ENTERPRISE', 'report-builder': 'ENTERPRISE',
  'operations-center': 'ENTERPRISE', team: 'ENTERPRISE', audit: 'ENTERPRISE', settings: 'ENTERPRISE',
};

export function requiredPlan(module) { return PLAN_REQUIREMENTS[module] || 'FREE'; }
export function planAllows(plan, module, status = 'Active') {
  const normalizedStatus = String(status || 'Active');
  if (['Expired', 'Past Due', 'Cancelled'].includes(normalizedStatus)) return requiredPlan(module) === 'FREE';
  return PLAN_LEVELS[normalizePlan(plan)] >= PLAN_LEVELS[requiredPlan(module)];
}
