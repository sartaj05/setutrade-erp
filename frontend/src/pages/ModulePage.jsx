import EnhancedModulePage from './EnhancedModulePage';
import ProductionModulePage from './ProductionModulePage';
import GrowthModulePage from './GrowthModulePage';

const productionModules = ['products','inventory','customers','orders','invoices','purchases','warehouses','quotations','payments','reports','team','settings','audit'];
const growthModules = ['delivery'];
const enhancedModules = ['ledger','barcode','whatsapp','tax','pricing','returns','field-sales','insights'];

export default function ModulePage({ module }) {
  if (productionModules.includes(module)) return <ProductionModulePage module={module} />;
  if (growthModules.includes(module)) return <GrowthModulePage module={module} />;
  if (enhancedModules.includes(module)) return <EnhancedModulePage module={module} />;
  return <ProductionModulePage module="reports" />;
}
