export const demoPurchases = [
  { pk: 1, id: 'PO-2026-084', supplier: 'Polycab India Supply', total: 186400, status: 'Partial', date: '20 Sep', expected: '23 Sep', items: 6 },
  { pk: 2, id: 'PO-2026-083', supplier: 'Havells Channel Partner', total: 124850, status: 'Sent', date: '19 Sep', expected: '24 Sep', items: 4 },
  { pk: 3, id: 'PO-2026-082', supplier: 'Legrand NCR Distribution', total: 96800, status: 'Received', date: '18 Sep', expected: '20 Sep', items: 3 },
  { pk: 4, id: 'PO-2026-081', supplier: 'GM Modular Supply Co.', total: 71420, status: 'Draft', date: '17 Sep', expected: '25 Sep', items: 5 },
];

export const demoSuppliers = [
  { pk: 1, id: 'S-001', name: 'Polycab India Supply', city: 'Delhi', outstanding: 212600 },
  { pk: 2, id: 'S-002', name: 'Havells Channel Partner', city: 'Noida', outstanding: 124850 },
  { pk: 3, id: 'S-003', name: 'Legrand NCR Distribution', city: 'Gurugram', outstanding: 0 },
];

export const demoLedger = [
  { customer: 'Sethi Hardware House', customerId: 'C-105', type: 'Invoice', reference: 'INV-2026-1164', amount: 124600, date: '18 Aug', due: '18 Sep', bucket: '1-30 days' },
  { customer: 'Metro Electricals', customerId: 'C-102', type: 'Invoice', reference: 'INV-2026-1171', amount: 38400, date: '09 Aug', due: '09 Sep', bucket: '1-30 days' },
  { customer: 'R.K. Trading Co.', customerId: 'C-101', type: 'Invoice', reference: 'INV-2026-1184', amount: 58240, date: '21 Sep', due: '28 Sep', bucket: 'Current' },
  { customer: 'Ahuja Enterprises', customerId: 'C-103', type: 'Payment', reference: 'RCPT-2026-422', amount: -76000, date: '20 Sep', due: '—', bucket: 'Current' },
  { customer: 'NCR Buildmart', customerId: 'C-104', type: 'Invoice', reference: 'INV-2026-1182', amount: 76750, date: '20 Sep', due: '25 Sep', bucket: 'Current' },
];

export const demoWarehouses = {
  warehouses: [
    { pk: 1, id: 'WH-DEL', name: 'Delhi Central', city: 'Delhi', stock: 580, reserved: 64 },
    { pk: 2, id: 'WH-NOI', name: 'Noida Hub', city: 'Noida', stock: 220, reserved: 22 },
    { pk: 3, id: 'WH-GGN', name: 'Gurugram Depot', city: 'Gurugram', stock: 145, reserved: 18 },
  ],
  transfers: [
    { pk: 1, id: 'TR-2026-031', from: 'Delhi Central', to: 'Noida Hub', status: 'In Transit', date: '21 Sep', units: 50 },
    { pk: 2, id: 'TR-2026-030', from: 'Delhi Central', to: 'Gurugram Depot', status: 'Received', date: '20 Sep', units: 34 },
    { pk: 3, id: 'TR-2026-029', from: 'Noida Hub', to: 'Delhi Central', status: 'Draft', date: '20 Sep', units: 18 },
  ],
};

export const demoBarcodes = [
  { sku: 'PC-25-RD', name: 'Polycab 2.5mm Wire Red', barcode: '8901002500017', stock: 7, unit: 'coil', location: 'A-01' },
  { sku: 'HA-LED-12', name: 'Havells 12W LED Bulb', barcode: '8901762048129', stock: 86, unit: 'pcs', location: 'B-07' },
  { sku: 'AN-MCB-32', name: 'Anchor 32A DP MCB', barcode: '8901442032036', stock: 24, unit: 'pcs', location: 'C-11' },
  { sku: 'GM-PLT-8', name: 'GM 8 Module Plate', barcode: '8906084407084', stock: 12, unit: 'pcs', location: 'D-04' },
];

export const demoWhatsAppDrafts = [
  { id: 'WA-260921-014', customer: 'R.K. Trading Co.', message: 'Need 20 Anchor 32A MCB and 10 Havells 12W LED bulbs', total: 11350, status: 'Draft', items: [{ sku: 'AN-MCB-32', name: 'Anchor 32A DP MCB', quantity: 20, unit: 'pcs', price: 495, available: 24 }, { sku: 'HA-LED-12', name: 'Havells 12W LED Bulb', quantity: 10, unit: 'pcs', price: 145, available: 86 }] },
  { id: 'WA-260921-013', customer: 'Metro Electricals', message: 'Send 5 coils Polycab 2.5mm red today', total: 10200, status: 'Quoted', items: [{ sku: 'PC-25-RD', name: 'Polycab 2.5mm Wire Red', quantity: 5, unit: 'coil', price: 2040, available: 7 }] },
];

export const demoTax = {
  invoices: [
    { id: 'INV-2026-1184', customer: 'R.K. Trading Co.', gstin: '09AABCR1234A1Z5', taxable: 49356, cgst: 4442, sgst: 4442, igst: 0, total: 58240, supplyType: 'Inter-state', placeOfSupply: 'Uttar Pradesh', einvoice: 'Ready', irn: '' },
    { id: 'INV-2026-1183', customer: 'Ahuja Enterprises', gstin: '07AAECA3344M1Z2', taxable: 64508, cgst: 5806, sgst: 5806, igst: 0, total: 76120, supplyType: 'Intra-state', placeOfSupply: 'Delhi', einvoice: 'Generated', irn: 'DEMO-IRN-1183' },
  ],
  notes: [
    { id: 'CN-2026-043', type: 'Credit Note', customer: 'Metro Electricals', invoice: 'INV-2026-1171', total: 4720, date: '19 Sep', reason: '2 damaged MCBs returned' },
    { id: 'DN-2026-011', type: 'Debit Note', customer: 'NCR Buildmart', invoice: 'INV-2026-1158', total: 2360, date: '16 Sep', reason: 'Rate difference adjustment' },
  ],
  integration: { mode: 'configurable', einvoice: false, ewayBill: false, message: 'Demo mode: connect an authorised provider for production e-invoice/e-way bill generation.' },
};

export const demoPricing = [
  { id: 1, name: 'Electrical Dealer Standard', customer: 'All dealer customers', validFrom: '2026-09-01', validTo: '2026-12-31', rules: [
    { sku: 'AN-MCB-32', product: 'Anchor 32A DP MCB', minQty: 1, price: 495, discount: 0, scheme: '' },
    { sku: 'AN-MCB-32', product: 'Anchor 32A DP MCB', minQty: 10, price: 465, discount: 6, scheme: '10+ dealer slab' },
    { sku: 'AN-MCB-32', product: 'Anchor 32A DP MCB', minQty: 50, price: 438, discount: 11.5, scheme: '50+ distributor slab' },
  ]},
  { id: 2, name: 'R.K. Trading Special', customer: 'R.K. Trading Co.', validFrom: '2026-09-15', validTo: '2026-10-15', rules: [
    { sku: 'HA-LED-12', product: 'Havells 12W LED Bulb', minQty: 20, price: 132, discount: 9, scheme: 'Buy 20+ at special rate' },
    { sku: 'PC-25-RD', product: 'Polycab 2.5mm Wire Red', minQty: 5, price: 1940, discount: 5, scheme: '5 coil project rate' },
  ]},
];

export const demoReturns = {
  returns: [
    { id: 'SR-2026-042', type: 'Sales Return', party: 'Metro Electricals', warehouse: 'Delhi Central', items: 2, total: 4720, date: '19 Sep', status: 'Inspected', reason: 'Damaged MCBs received from customer' },
    { id: 'PR-2026-018', type: 'Purchase Return', party: 'Polycab India Supply', warehouse: 'Delhi Central', items: 1, total: 9100, date: '18 Sep', status: 'Open', reason: 'Outer insulation damaged in transit' },
    { id: 'SR-2026-041', type: 'Sales Return', party: 'NCR Buildmart', warehouse: 'Gurugram Depot', items: 3, total: 6840, date: '17 Sep', status: 'Completed', reason: 'Incorrect model ordered' },
  ],
  adjustments: [
    { id: 'ADJ-2026-071', type: 'Damaged', product: 'Havells 12W LED Bulb', sku: 'HA-LED-12', warehouse: 'Noida Hub', quantity: -4, date: '21 Sep', reason: 'Broken during shelf handling' },
    { id: 'ADJ-2026-070', type: 'Count correction', product: 'GM 8 Module Plate', sku: 'GM-PLT-8', warehouse: 'Delhi Central', quantity: 2, date: '20 Sep', reason: 'Cycle count correction' },
  ],
};

export const demoFieldSales = {
  target: { sales: 1200000, collection: 600000 },
  visits: [
    { id: 1, salesperson: 'Rohit Bansal', customer: 'R.K. Trading Co.', city: 'Ghaziabad', date: '21 Sep', status: 'Visited', territory: 'Ghaziabad East', orderValue: 58240, collection: 18000, notes: 'Order confirmed; next visit Friday.' },
    { id: 2, salesperson: 'Rohit Bansal', customer: 'Metro Electricals', city: 'Noida', date: '21 Sep', status: 'Visited', territory: 'Noida Central', orderValue: 38400, collection: 12000, notes: 'Collection partial; customer asked for MCB quote.' },
    { id: 3, salesperson: 'Rohit Bansal', customer: 'NCR Buildmart', city: 'Gurugram', date: '21 Sep', status: 'Planned', territory: 'Gurugram North', orderValue: 0, collection: 0, notes: 'Discuss project cable requirement.' },
    { id: 4, salesperson: 'Rohit Bansal', customer: 'Sethi Hardware House', city: 'Faridabad', date: '22 Sep', status: 'Planned', territory: 'Faridabad', orderValue: 0, collection: 0, notes: 'Priority collection follow-up.' },
  ],
};

export const demoInsights = {
  metrics: { sales: 4286400, stockValue: 3184500, receivable: 472350, highRisk: 3 },
  reorder: [
    { sku: 'PC-25-RD', product: 'Polycab 2.5mm Wire Red', warehouse: 'Delhi Central', stock: 7, dailySales: 3.2, leadTime: 5, suggested: 50, daysCover: 2.2, risk: 'High' },
    { sku: 'GM-PLT-8', product: 'GM 8 Module Plate', warehouse: 'Delhi Central', stock: 12, dailySales: 2.1, leadTime: 7, suggested: 36, daysCover: 5.7, risk: 'High' },
    { sku: 'LE-FAN-48', product: 'Legrand Exhaust Fan 48W', warehouse: 'Gurugram Depot', stock: 9, dailySales: 1.1, leadTime: 6, suggested: 18, daysCover: 8.2, risk: 'Medium' },
    { sku: 'AN-MCB-32', product: 'Anchor 32A DP MCB', warehouse: 'Noida Hub', stock: 24, dailySales: 2.4, leadTime: 4, suggested: 20, daysCover: 10, risk: 'Low' },
  ],
  receivables: [
    { customer: 'Sethi Hardware House', city: 'Faridabad', outstanding: 124600, limit: 180000 },
    { customer: 'NCR Buildmart', city: 'Gurugram', outstanding: 76750, limit: 250000 },
    { customer: 'R.K. Trading Co.', city: 'Ghaziabad', outstanding: 58240, limit: 150000 },
  ],
};
