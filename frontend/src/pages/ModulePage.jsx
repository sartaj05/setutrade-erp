import EnhancedModulePage from './EnhancedModulePage';
import ProductionModulePage from './ProductionModulePage';
import GrowthModulePage from './GrowthModulePage';
import ExpansionModulePage from './ExpansionModulePage';
import StrategicModulePage from './StrategicModulePage';

const productionModules = ['products','inventory','customers','orders','invoices','purchases','warehouses','quotations','payments','reports','team','settings','audit'];
const growthModules = ['delivery','approvals','invoice-ocr','accounting','offline','subscription','forecasting','assistant'];
const expansionModules = ['collections','wms','supplier-portal-admin','automations','channels','distribution-network'];
const strategicModules = ['crm'];
const enhancedModules = ['ledger','barcode','whatsapp','tax','pricing','returns','field-sales','insights'];

export default function ModulePage({ module }) {
  if (productionModules.includes(module)) return <ProductionModulePage module={module} />;
  if (growthModules.includes(module)) return <GrowthModulePage module={module} />;
  if (expansionModules.includes(module)) return <ExpansionModulePage module={module} />;
  if (strategicModules.includes(module)) return <StrategicModulePage module={module} />;
  if (enhancedModules.includes(module)) return <EnhancedModulePage module={module} />;
  return <ProductionModulePage module="reports" />;
}
