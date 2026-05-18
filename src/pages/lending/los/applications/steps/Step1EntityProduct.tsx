import { Search } from 'lucide-react';
import { useState, useEffect } from 'react';

import { useWizard } from '@/components/lending/wizard/WizardContext';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

// Entity + product pickers will be wired to the real list endpoints
// (/lending/entities/active and /lending/products/active) once the
// step is hooked up to react-query. For now the lists start empty
// so the wizard doesn't display fabricated names.
const mockEntities: {
  id: string;
  code: string;
  name: string;
  type: string;
  pan: string;
}[] = [];

const mockProducts: {
  id: string;
  code: string;
  name: string;
  category: string;
  minAmount: number;
  maxAmount: number;
}[] = [];

export default function Step1EntityProduct() {
  const { data, updateStepData, setValidation } = useWizard();
  const stepData = (data['entity-product'] || {}) as Record<string, string>;

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEntity, setSelectedEntity] = useState<(typeof mockEntities)[0] | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<(typeof mockProducts)[0] | null>(null);

  // Initialize from existing data
  useEffect(() => {
    if (stepData.entityId) {
      const entity = mockEntities.find((e) => e.id === stepData.entityId);
      setSelectedEntity(entity || null);
    }
    if (stepData.productId) {
      const product = mockProducts.find((p) => p.id === stepData.productId);
      setSelectedProduct(product || null);
    }
  }, [stepData.entityId, stepData.productId]);

  // Update validation when selections change
  useEffect(() => {
    const isValid = Boolean(selectedEntity && selectedProduct);
    setValidation('entity-product', isValid);
  }, [selectedEntity, selectedProduct, setValidation]);

  const filteredEntities = mockEntities.filter(
    (e) =>
      e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.pan.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const handleEntitySelect = (entityId: string) => {
    const entity = mockEntities.find((e) => e.id === entityId);
    setSelectedEntity(entity || null);
    updateStepData('entity-product', { ...stepData, entityId });
  };

  const handleProductSelect = (productId: string) => {
    const product = mockProducts.find((p) => p.id === productId);
    setSelectedProduct(product || null);
    updateStepData('entity-product', { ...stepData, productId });
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
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium">{entity.name}</p>
                    <p className="font-mono text-sm text-muted-foreground">{entity.code}</p>
                  </div>
                  <span className="rounded bg-gray-100 px-2 py-1 text-xs">{entity.type}</span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">PAN: {entity.pan}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {selectedEntity && (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <p className="text-sm font-medium text-blue-700">Selected Entity</p>
            <p className="font-medium">{selectedEntity.name}</p>
            <p className="text-sm text-muted-foreground">
              {selectedEntity.code} | PAN: {selectedEntity.pan}
            </p>
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
            <div className="rounded-lg border border-green-200 bg-green-50 p-4">
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
