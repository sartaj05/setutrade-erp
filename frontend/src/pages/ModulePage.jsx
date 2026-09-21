import EnhancedModulePage from './EnhancedModulePage';
import ProductionModulePage from './ProductionModulePage';

const productionModules = ['products','inventory','customers','orders','invoices','purchases','warehouses','quotations','payments','reports','team','settings','audit'];
const enhancedModules = ['ledger','barcode','whatsapp','tax','pricing','returns','field-sales','insights'];

export default function ModulePage({ module }) {
  if (productionModules.includes(module)) return <ProductionModulePage module={module} />;
  if (enhancedModules.includes(module)) return <EnhancedModulePage module={module} />;
  return <ProductionModulePage module="reports" />;
}
