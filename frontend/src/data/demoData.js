export const demoAccounts = [
  { id: 1, name: 'Arjun Khanna', email: 'owner@setustock.demo', password: 'demo123', role: 'OWNER', business: 'Khanna Electrical Distributors' },
  { id: 2, name: 'Meera Sethi', email: 'manager@setustock.demo', password: 'demo123', role: 'MANAGER', business: 'Khanna Electrical Distributors' },
  { id: 3, name: 'Rohit Bansal', email: 'sales@setustock.demo', password: 'demo123', role: 'SALES', business: 'Khanna Electrical Distributors' },
  { id: 4, name: 'Imran Ali', email: 'warehouse@setustock.demo', password: 'demo123', role: 'WAREHOUSE', business: 'Khanna Electrical Distributors' },
  { id: 5, name: 'Nisha Gupta', email: 'accountant@setustock.demo', password: 'demo123', role: 'ACCOUNTANT', business: 'Khanna Electrical Distributors' },
];

export const permissions = {
  OWNER: ['dashboard', 'products', 'inventory', 'customers', 'orders', 'invoices', 'purchases', 'ledger', 'warehouses', 'barcode', 'whatsapp', 'tax', 'pricing', 'returns', 'field-sales', 'insights', 'quotations', 'payments', 'reports', 'team', 'settings'],
  MANAGER: ['dashboard', 'products', 'inventory', 'customers', 'orders', 'invoices', 'purchases', 'ledger', 'warehouses', 'barcode', 'whatsapp', 'tax', 'pricing', 'returns', 'field-sales', 'insights', 'quotations', 'payments', 'reports'],
  SALES: ['dashboard', 'customers', 'orders', 'invoices', 'ledger', 'whatsapp', 'tax', 'pricing', 'field-sales', 'quotations', 'payments'],
  WAREHOUSE: ['dashboard', 'products', 'inventory', 'orders', 'purchases', 'warehouses', 'barcode', 'returns', 'insights'],
  ACCOUNTANT: ['dashboard', 'customers', 'orders', 'invoices', 'purchases', 'ledger', 'tax', 'returns', 'insights', 'payments', 'reports'],
};

export const roleHomeCopy = {
  OWNER: 'Full business visibility across sales, stock and receivables.',
  MANAGER: 'Keep daily operations moving and exceptions under control.',
  SALES: 'Stay on top of customer orders, quotations and collections.',
  WAREHOUSE: 'Focus on stock health, picking and dispatch readiness.',
  ACCOUNTANT: 'Track outstanding balances, invoices and collection movement.',
};

export const demoDashboard = {
  metrics: {
    salesToday: 184240,
    salesMonth: 4286400,
    receivable: 472350,
    stockValue: 3184500,
    openOrders: 34,
    lowStock: 8,
  },
  recentOrders: [
    { id: 'SO-1097', customer: 'R.K. Trading Co.', total: 58240, status: 'Ready', payment: 'Credit', date: '21 Sep' },
    { id: 'SO-1096', customer: 'Metro Electricals', total: 38400, status: 'Processing', payment: 'Overdue', date: '21 Sep' },
    { id: 'SO-1095', customer: 'Ahuja Enterprises', total: 76120, status: 'Packed', payment: 'Paid', date: '20 Sep' },
    { id: 'SO-1094', customer: 'NCR Buildmart', total: 29480, status: 'Dispatched', payment: 'Credit', date: '20 Sep' },
  ],
  activity: [
    { title: 'Payment received', text: '₹24,000 from Ahuja Enterprises', time: '22 min ago', tone: 'success' },
    { title: 'Low stock alert', text: 'Polycab 2.5mm wire reached 7 coils', time: '48 min ago', tone: 'warning' },
    { title: 'Order ready', text: 'SO-1097 is ready for dispatch', time: '1 hr ago', tone: 'info' },
  ],
};

export const demoProducts = [
  { sku: 'PC-25-RD', name: 'Polycab 2.5mm Wire Red', category: 'Wires & Cables', stock: 7, unit: 'coil', buy: 1820, sell: 2040, reorder: 12, location: 'A-01' },
  { sku: 'HA-LED-12', name: 'Havells 12W LED Bulb', category: 'Lighting', stock: 86, unit: 'pcs', buy: 118, sell: 145, reorder: 30, location: 'B-07' },
  { sku: 'AN-MCB-32', name: 'Anchor 32A DP MCB', category: 'Switchgear', stock: 24, unit: 'pcs', buy: 412, sell: 495, reorder: 20, location: 'C-11' },
  { sku: 'GM-PLT-8', name: 'GM 8 Module Plate', category: 'Switches', stock: 12, unit: 'pcs', buy: 176, sell: 225, reorder: 15, location: 'D-04' },
  { sku: 'RR-4SQ-BK', name: 'RR Kabel 4 sq mm Black', category: 'Wires & Cables', stock: 18, unit: 'coil', buy: 2960, sell: 3290, reorder: 10, location: 'A-04' },
  { sku: 'LE-FAN-48', name: 'Legrand Exhaust Fan 48W', category: 'Fans', stock: 9, unit: 'pcs', buy: 1780, sell: 2140, reorder: 8, location: 'E-02' },
];

export const demoCustomers = [
  { id: 'C-101', name: 'R.K. Trading Co.', city: 'Ghaziabad', phone: '9810012233', outstanding: 58240, limit: 150000, due: '28 Sep', status: 'Current' },
  { id: 'C-102', name: 'Metro Electricals', city: 'Noida', phone: '9871123456', outstanding: 38400, limit: 100000, due: '09 Sep', status: 'Overdue' },
  { id: 'C-103', name: 'Ahuja Enterprises', city: 'Delhi', phone: '9899011122', outstanding: 0, limit: 200000, due: '—', status: 'Clear' },
  { id: 'C-104', name: 'NCR Buildmart', city: 'Gurugram', phone: '9958012211', outstanding: 76750, limit: 250000, due: '25 Sep', status: 'Current' },
  { id: 'C-105', name: 'Sethi Hardware House', city: 'Faridabad', phone: '9818817717', outstanding: 124600, limit: 180000, due: '18 Sep', status: 'Overdue' },
];

export const demoInvoices = [
  { id: 'INV-2026-1184', order: 'SO-1097', customer: 'R.K. Trading Co.', gstin: '09AABCR1234A1Z5', taxable: 49356, tax: 8884, total: 58240, status: 'Unpaid', date: '21 Sep' },
  { id: 'INV-2026-1183', order: 'SO-1095', customer: 'Ahuja Enterprises', gstin: '07AAECA3344M1Z2', taxable: 64508, tax: 11612, total: 76120, status: 'Paid', date: '20 Sep' },
  { id: 'INV-2026-1182', order: 'SO-1094', customer: 'NCR Buildmart', gstin: '06AAGFN7788B1Z9', taxable: 24983, tax: 4497, total: 29480, status: 'Credit', date: '20 Sep' },
];
