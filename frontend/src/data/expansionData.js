export const demoCollections = {
  summary: { receivable: 472350, openTasks: 8, promiseAmount: 164000, unmatched: 2 },
  tasks: [
    { id: 1, customer: 'Sethi Hardware House', amount: 124600, due: '2026-09-21', priority: 'High', status: 'Open', assignee: 'Rohit Bansal' },
    { id: 2, customer: 'Metro Electricals', amount: 38400, due: '2026-09-21', priority: 'High', status: 'Contacted', assignee: 'Rohit Bansal' },
    { id: 3, customer: 'R.K. Trading Co.', amount: 58240, due: '2026-09-28', priority: 'Normal', status: 'Open', assignee: 'Rohit Bansal' },
  ],
  promises: [
    { id: 1, customer: 'Sethi Hardware House', amount: 50000, date: '2026-09-25', status: 'Open' },
    { id: 2, customer: 'NCR Buildmart', amount: 42000, date: '2026-09-24', status: 'Open' },
  ],
  transactions: [
    { id: 1, reference: 'UPI-826144', customer: 'Ahuja Enterprises', amount: 24000, method: 'UPI', date: '2026-09-21', status: 'Matched' },
    { id: 2, reference: 'BANK-7721', customer: 'R.K. Trading Co.', amount: 15000, method: 'Bank', date: '2026-09-21', status: 'Partial' },
  ],
};

export const demoWms = {
  bins: [
    { id: 1, code: 'A-01-01', zone: 'Fast Moving', warehouse: 'Delhi Central', capacity: 120 },
    { id: 2, code: 'A-01-02', zone: 'Fast Moving', warehouse: 'Delhi Central', capacity: 120 },
    { id: 3, code: 'C-04-03', zone: 'Switchgear', warehouse: 'Noida Hub', capacity: 80 },
  ],
  picks: [
    { id: 1, pickNo: 'PICK-260921-019', warehouse: 'Delhi Central', status: 'Picking', lines: 6 },
    { id: 2, pickNo: 'PICK-260921-018', warehouse: 'Delhi Central', status: 'Complete', lines: 4 },
  ],
  counts: [
    { id: 1, warehouse: 'Delhi Central', bin: 'A-01-01', product: 'Polycab 2.5mm Wire Red', expected: 7, counted: 6, status: 'Counted' },
  ],
};

export const demoSupplierPortalAdmin = {
  submissions: [
    { id: 1, supplier: 'Polycab India Supply', po: 'PO-2026-084', type: 'ETA', status: 'Submitted', payload: { eta: '2026-09-23', note: 'Truck dispatched from Bhiwadi.' } },
    { id: 2, supplier: 'Havells Channel Partner', po: 'PO-2026-081', type: 'INVOICE', status: 'Submitted', payload: { invoiceNo: 'HV-88321', fileName: 'HV-88321.pdf' } },
  ],
};

export const demoAutomations = {
  rules: [
    { id: 1, name: 'Overdue > ₹50k collection escalation', event: 'invoice.overdue', conditions: { outstanding: { gte: 50000 } }, actions: [{ type: 'create_collection_task' }, { type: 'notify', title: 'High-value overdue customer' }], active: true },
    { id: 2, name: 'Low stock buyer alert', event: 'stock.low', conditions: { daysCover: { gt: 0 } }, actions: [{ type: 'notify', title: 'Reorder review required' }], active: true },
  ],
  runs: [
    { id: 1, rule: 'Overdue > ₹50k collection escalation', event: 'invoice.overdue', status: 'Completed', actions: ['create_collection_task', 'notify'], createdAt: '2026-09-21T11:40:00+05:30' },
  ],
};

export const demoChannels = {
  channels: [
    { id: 1, name: 'Khanna Web Catalogue', provider: 'WEBSITE', active: true, storeId: 'web-delhi-01', lastSync: '2026-09-21T12:20:00+05:30' },
    { id: 2, name: 'ONDC Seller Adapter', provider: 'ONDC', active: false, storeId: 'pending-credentials', lastSync: null },
  ],
  orders: [
    { id: 1, externalId: 'WEB-44182', channel: 'Khanna Web Catalogue', provider: 'WEBSITE', customer: 'Bright Electricals', phone: '9811004411', total: 26480, status: 'New', receivedAt: '2026-09-21T11:52:00+05:30', items: [{ sku: 'AN-MCB-32', name: 'Anchor 32A DP MCB', qty: 20, price: 495, matched: true }] },
  ],
};

export const demoNetworks = {
  ownedNetworks: [{ id: 1, name: 'North India Electrical Network', code: 'NCR-ELEC', members: [
    { id: 1, company: 'Khanna Electrical Distributors', region: 'Delhi', territory: 'Central Delhi', shareInventory: true, shareSales: true, snapshot: { date: '2026-09-21', inventoryValue: 3184500, stockUnits: 156, secondarySales: 4286400, openOrders: 34, products: [] } },
    { id: 2, company: 'Noida Channel Demo', region: 'Uttar Pradesh', territory: 'Noida', shareInventory: true, shareSales: true, snapshot: { date: '2026-09-21', inventoryValue: 1684200, stockUnits: 98, secondarySales: 2248000, openOrders: 17, products: [] } },
    { id: 3, company: 'Gurugram Channel Demo', region: 'Haryana', territory: 'Gurugram', shareInventory: true, shareSales: true, snapshot: { date: '2026-09-21', inventoryValue: 2014600, stockUnits: 121, secondarySales: 2672000, openOrders: 21, products: [] } },
  ] }],
  memberships: [],
};
