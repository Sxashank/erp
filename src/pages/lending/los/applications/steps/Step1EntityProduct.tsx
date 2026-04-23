import { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useWizard } from '@/components/lending/wizard/WizardContext';

// Mock data for entities
const mockEntities = [
  { id: '1', code: 'ENT/2024/00001', name: 'Metro Industries Pvt Ltd', type: 'CORPORATE', pan: 'AAACM1234A' },
  { id: '2', code: 'ENT/2024/00002', name: 'Sunrise Enterprises', type: 'LLP', pan: 'AABFS5678B' },
  { id: '3', code: 'ENT/2024/00003', name: 'Global Trading Co', type: 'PARTNERSHIP', pan: 'AACGT9012C' },
  { id: '4', code: 'ENT/2024/00004', name: 'Rajesh Kumar', type: 'INDIVIDUAL', pan: 'AADPR3456D' },
];

const mockProducts = [
  { id: '1', code: 'TL-CORP', name: 'Term Loan - Corporate', category: 'TERM_LOAN', minAmount: 10000000, maxAmount: 5000000000 },
  { id: '2', code: 'TL-PROJ', name: 'Term Loan - Project Finance', category: 'TERM_LOAN', minAmount: 50000000, maxAmount: 10000000000 },
  { id: '3', code: 'WC-CC', name: 'Working Capital - Cash Credit', category: 'WORKING_CAPITAL', minAmount: 5000000, maxAmount: 1000000000 },
  { id: '4', code: 'LAP', name: 'Loan Against Property', category: 'LAP', minAmount: 2500000, maxAmount: 500000000 },
];

export default function Step1EntityProduct() {
  const { data, updateStepData, setValidation } = useWizard();
  const stepData = (data['entity-product'] || {}) as Record<string, string>;

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEntity, setSelectedEntity] = useState<typeof mockEntities[0] | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<typeof mockProducts[0] | null>(null);

  // Initialize from existing data
  useEffect(() => {
    if (stepData.entity_id) {
      const entity = mockEntities.find((e) => e.id === stepData.entity_id);
      setSelectedEntity(entity || null);
    }
    if (stepData.product_id) {
      const product = mockProducts.find((p) => p.id === stepData.product_id);
      setSelectedProduct(product || null);
    }
  }, [stepData.entity_id, stepData.product_id]);

  // Update validation when selections change
  useEffect(() => {
    const isValid = Boolean(selectedEntity && selectedProduct);
    setValidation('entity-product', isValid);
  }, [selectedEntity, selectedProduct, setValidation]);

  const filteredEntities = mockEntities.filter(
    (e) =>
      e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.pan.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleEntitySelect = (entityId: string) => {
    const entity = mockEntities.find((e) => e.id === entityId);
    setSelectedEntity(entity || null);
    updateStepData('entity-product', { ...stepData, entity_id: entityId });
  };

  const handleProductSelect = (productId: string) => {
    const product = mockProducts.find((p) => p.id === productId);
    setSelectedProduct(product || null);
    updateStepData('entity-product', { ...stepData, product_id: productId });
  };

  return (
    <div className="space-y-8">
      {/* Entity Selection */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium">Select Entity/Borrower</h3>
          <p className="text-sm text-muted-foreground">
            Search and select the borrower for this loan application
          </p>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by entity name, code, or PAN..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          {filteredEntities.map((entity) => (
            <Card
              key={entity.id}
              className={`cursor-pointer transition-all ${
                selectedEntity?.id === entity.id
                  ? 'border-blue-500 ring-2 ring-blue-200'
                  : 'hover:border-gray-300'
              }`}
              onClick={() => handleEntitySelect(entity.id)}
            >
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium">{entity.name}</p>
                    <p className="text-sm text-muted-foreground font-mono">{entity.code}</p>
                  </div>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">{entity.type}</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">PAN: {entity.pan}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {selectedEntity && (
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-sm font-medium text-blue-700">Selected Entity</p>
            <p className="font-medium">{selectedEntity.name}</p>
            <p className="text-sm text-muted-foreground">{selectedEntity.code} | PAN: {selectedEntity.pan}</p>
          </div>
        )}
      </div>

      {/* Product Selection */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium">Select Loan Product</h3>
          <p className="text-sm text-muted-foreground">
            Choose the loan product for this application
          </p>
        </div>

        <div className="grid gap-4">
          <div>
            <Label>Loan Product</Label>
            <Select value={selectedProduct?.id || ''} onValueChange={handleProductSelect}>
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Select a loan product" />
              </SelectTrigger>
              <SelectContent>
                {mockProducts.map((product) => (
                  <SelectItem key={product.id} value={product.id}>
                    <div className="flex flex-col">
                      <span>{product.name}</span>
                      <span className="text-xs text-muted-foreground">{product.code}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedProduct && (
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-sm font-medium text-green-700">Selected Product</p>
              <p className="font-medium">{selectedProduct.name}</p>
              <p className="text-sm text-muted-foreground">
                Min: ₹ {(selectedProduct.minAmount / 10000000).toFixed(2)} Cr | Max: ₹{' '}
                {(selectedProduct.maxAmount / 10000000).toFixed(2)} Cr
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
