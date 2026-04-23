import { useState, useEffect } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useWizard } from '@/components/lending/wizard/WizardContext';
import { AmountInput } from '@/components/lending/common/AmountInput';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';

interface Security {
  id: string;
  security_type: string;
  nature: string;
  description: string;
  value: number;
  margin: number;
}

interface Step4Props {
  applicationId?: string;
}

export default function Step4Security({ applicationId }: Step4Props) {
  const { setValidation } = useWizard();
  const [securities, setSecurities] = useState<Security[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [currentSecurity, setCurrentSecurity] = useState<Partial<Security>>({});

  useEffect(() => {
    // Security is optional, always valid
    setValidation('security', true);
  }, [setValidation]);

  const handleAddSecurity = () => {
    if (currentSecurity.security_type && currentSecurity.nature && currentSecurity.value) {
      const newSecurity: Security = {
        id: Date.now().toString(),
        security_type: currentSecurity.security_type || '',
        nature: currentSecurity.nature || '',
        description: currentSecurity.description || '',
        value: currentSecurity.value || 0,
        margin: currentSecurity.margin || 0,
      };
      setSecurities([...securities, newSecurity]);
      setCurrentSecurity({});
      setShowForm(false);
    }
  };

  const handleRemoveSecurity = (id: string) => {
    setSecurities(securities.filter((s) => s.id !== id));
  };

  const totalSecurityValue = securities.reduce((sum, s) => sum + s.value, 0);
  const totalNetValue = securities.reduce((sum, s) => sum + (s.value * (100 - s.margin)) / 100, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">Security & Collateral</h3>
          <p className="text-sm text-muted-foreground">
            Add collateral and security details for this loan
          </p>
        </div>
        <Button onClick={() => setShowForm(true)} disabled={showForm}>
          <Plus className="mr-2 h-4 w-4" />
          Add Security
        </Button>
      </div>

      {/* Summary */}
      {securities.length > 0 && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">Total Security Value</p>
              <AmountDisplay amount={totalSecurityValue} abbreviated className="text-xl font-bold" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">Net Value (After Margin)</p>
              <AmountDisplay amount={totalNetValue} abbreviated className="text-xl font-bold text-green-600" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">Securities Added</p>
              <p className="text-xl font-bold">{securities.length}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Add Security Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Add Security</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Security Type *</Label>
                <Select
                  value={currentSecurity.security_type || ''}
                  onValueChange={(value) =>
                    setCurrentSecurity({ ...currentSecurity, security_type: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PRIMARY">Primary Security</SelectItem>
                    <SelectItem value="COLLATERAL">Collateral Security</SelectItem>
                    <SelectItem value="PERSONAL_GUARANTEE">Personal Guarantee</SelectItem>
                    <SelectItem value="CORPORATE_GUARANTEE">Corporate Guarantee</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Nature of Security *</Label>
                <Select
                  value={currentSecurity.nature || ''}
                  onValueChange={(value) =>
                    setCurrentSecurity({ ...currentSecurity, nature: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select nature" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="IMMOVABLE_PROPERTY">Immovable Property</SelectItem>
                    <SelectItem value="MOVABLE_ASSETS">Movable Assets</SelectItem>
                    <SelectItem value="FIXED_DEPOSIT">Fixed Deposit</SelectItem>
                    <SelectItem value="RECEIVABLES">Receivables</SelectItem>
                    <SelectItem value="INVENTORY">Inventory</SelectItem>
                    <SelectItem value="SHARES">Shares/Securities</SelectItem>
                    <SelectItem value="GUARANTEE">Guarantee</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Security Value *</Label>
                <AmountInput
                  value={currentSecurity.value || 0}
                  onChange={(value) =>
                    setCurrentSecurity({ ...currentSecurity, value })
                  }
                  placeholder="Enter security value"
                />
              </div>

              <div className="space-y-2">
                <Label>Margin (%)</Label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={currentSecurity.margin || ''}
                  onChange={(e) =>
                    setCurrentSecurity({
                      ...currentSecurity,
                      margin: parseFloat(e.target.value),
                    })
                  }
                  placeholder="e.g., 25"
                />
              </div>

              <div className="space-y-2 md:col-span-2">
                <Label>Description</Label>
                <Textarea
                  value={currentSecurity.description || ''}
                  onChange={(e) =>
                    setCurrentSecurity({ ...currentSecurity, description: e.target.value })
                  }
                  placeholder="Describe the security..."
                  rows={2}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowForm(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddSecurity}>Add Security</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Securities List */}
      <div className="space-y-3">
        {securities.map((security) => (
          <Card key={security.id}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{security.nature.replace(/_/g, ' ')}</span>
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                      {security.security_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  {security.description && (
                    <p className="text-sm text-muted-foreground">{security.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <AmountDisplay amount={security.value} abbreviated className="font-medium" />
                    <p className="text-xs text-muted-foreground">
                      Net: <AmountDisplay
                        amount={(security.value * (100 - security.margin)) / 100}
                        abbreviated
                      />
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRemoveSecurity(security.id)}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {securities.length === 0 && !showForm && (
          <div className="text-center py-12 text-muted-foreground">
            No securities added yet. Click "Add Security" to add collateral details.
          </div>
        )}
      </div>
    </div>
  );
}
