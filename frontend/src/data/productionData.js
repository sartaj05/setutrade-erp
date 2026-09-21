export const demoQuotations = [
  { pk: 1, id: 'QT-260921-104', customer: 'R.K. Trading Co.', customerId: 1, date: '21 Sep', validUntil: '2026-09-28', status: 'Sent', total: 64900, warehouse: 'Delhi Central', order: null, items: [{ productId: 3, product: 'Anchor 32A DP MCB', sku: 'AN-MCB-32', quantity: 100, unitPrice: 465, total: 54870 }] },
  { pk: 2, id: 'QT-260920-098', customer: 'NCR Buildmart', customerId: 4, date: '20 Sep', validUntil: '2026-09-27', status: 'Accepted', total: 118000, warehouse: 'Gurugram Depot', order: null, items: [] },
];

export const demoPayments = [
  { id: 'RCPT-260921-442', party: 'R.K. Trading Co.', amount: 18000, method: 'UPI', date: '21 Sep', partyType: 'customer' },
  { id: 'RCPT-260920-439', party: 'Ahuja Enterprises', amount: 76000, method: 'Bank', date: '20 Sep', partyType: 'customer' },
  { id: 'SPAY-260920-117', party: 'Polycab India Supply', amount: 90000, method: 'Bank', date: '20 Sep', partyType: 'supplier' },
];

export const demoReports = {
  sales: 4286400, collections: 1284000, purchases: 1278000, receivable: 472350,
  payable: 337450, stockValue: 3184500,
  topCustomers: [
    { name: 'R.K. Trading Co.', sales: 684200 }, { name: 'NCR Buildmart', sales: 598400 },
    { name: 'Ahuja Enterprises', sales: 521800 }, { name: 'Metro Electricals', sales: 412600 },
  ],
};

export const demoTeam = [
  { id: 1, name: 'Arjun Khanna', email: 'owner@setustock.demo', role: 'OWNER', branch: 'Delhi HQ', active: true },
  { id: 2, name: 'Meera Sethi', email: 'manager@setustock.demo', role: 'MANAGER', branch: 'Delhi HQ', active: true },
  { id: 3, name: 'Rohit Bansal', email: 'sales@setustock.demo', role: 'SALES', branch: 'Delhi HQ', active: true },
  { id: 4, name: 'Imran Ali', email: 'warehouse@setustock.demo', role: 'WAREHOUSE', branch: 'Delhi HQ', active: true },
  { id: 5, name: 'Nisha Gupta', email: 'accountant@setustock.demo', role: 'ACCOUNTANT', branch: 'Delhi HQ', active: true },
];

export const demoSettings = {
  id: 1, name: 'Khanna Electrical Distributors', slug: 'khanna-electrical', gstin: '07AAAPK1234K1Z5', pan: 'AAAPK1234K', state: 'Delhi',
  address: 'Bhagirath Palace, Chandni Chowk, Delhi 110006', phone: '011-41234567', email: 'accounts@khanna.demo', bank_name: 'Demo Bank', bank_account: 'XXXX1206', ifsc: 'DEMO0001206', upi_id: 'khanna@upi', logo_url: '', invoice_prefix: 'INV-2026', financial_year_start: 4,
  branches: [{ id: 1, code: 'DEL', name: 'Delhi HQ', city: 'Delhi', gstin: '07AAAPK1234K1Z5', phone: '011-41234567' }], demoMode: true,
};

export const demoAudit = [
  { id: 1, action: 'create', entity: 'Order', entityId: '1097', summary: 'Created order SO-1097', actor: 'Rohit Bansal', time: '2026-09-21T10:28:00+05:30', changes: { total: 58240 } },
  { id: 2, action: 'receive', entity: 'PurchaseOrder', entityId: '84', summary: 'Received goods for PO-2026-084', actor: 'Imran Ali', time: '2026-09-21T09:44:00+05:30', changes: { grn: 'GRN-2026-044' } },
  { id: 3, action: 'create', entity: 'Payment', entityId: '442', summary: 'Recorded receipt RCPT-260921-442', actor: 'Nisha Gupta', time: '2026-09-21T09:15:00+05:30', changes: { amount: 18000 } },
];

export const demoNotifications = [
  { id: 1, title: 'Low stock needs attention', message: 'Polycab 2.5mm Wire Red is below its reorder level.', level: 'warning', module: 'insights', entityId: '1', read: false, time: '2026-09-21T10:10:00+05:30' },
  { id: 2, title: 'Collections follow-up', message: 'Two customer balances are overdue.', level: 'critical', module: 'ledger', entityId: '', read: false, time: '2026-09-21T09:40:00+05:30' },
];
