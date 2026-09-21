export const demoPurchases = [
  { id: 'PO-2026-084', supplier: 'Polycab India Supply', total: 186400, status: 'Partial', date: '20 Sep', expected: '23 Sep', items: 6 },
  { id: 'PO-2026-083', supplier: 'Havells Channel Partner', total: 124850, status: 'Sent', date: '19 Sep', expected: '24 Sep', items: 4 },
  { id: 'PO-2026-082', supplier: 'Legrand NCR Distribution', total: 96800, status: 'Received', date: '18 Sep', expected: '20 Sep', items: 3 },
  { id: 'PO-2026-081', supplier: 'GM Modular Supply Co.', total: 71420, status: 'Draft', date: '17 Sep', expected: '25 Sep', items: 5 },
];

export const demoSuppliers = [
  { id: 'S-001', name: 'Polycab India Supply', city: 'Delhi', outstanding: 212600 },
  { id: 'S-002', name: 'Havells Channel Partner', city: 'Noida', outstanding: 124850 },
  { id: 'S-003', name: 'Legrand NCR Distribution', city: 'Gurugram', outstanding: 0 },
];

export const demoLedger = [
  { customer: 'Sethi Hardware House', customerId: 'C-105', type: 'Invoice', reference: 'INV-2026-1164', amount: 124600, date: '18 Aug', due: '18 Sep', bucket: '1-30 days' },
  { customer: 'Metro Electricals', customerId: 'C-102', type: 'Invoice', reference: 'INV-2026-1171', amount: 38400, date: '09 Aug', due: '09 Sep', bucket: '1-30 days' },
  { customer: 'R.K. Trading Co.', customerId: 'C-101', type: 'Invoice', reference: 'INV-2026-1184', amount: 58240, date: '21 Sep', due: '28 Sep', bucket: 'Current' },
  { customer: 'Ahuja Enterprises', customerId: 'C-103', type: 'Payment', reference: 'RCPT-2026-422', amount: -76000, date: '20 Sep', due: '—', bucket: 'Current' },
  { customer: 'NCR Buildmart', customerId: 'C-104', type: 'Invoice', reference: 'INV-2026-1182', amount: 76750, date: '20 Sep', due: '25 Sep', bucket: 'Current' },
];
