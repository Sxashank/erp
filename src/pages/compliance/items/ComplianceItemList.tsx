/**
 * Compliance Item List Page
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Edit, Trash2, Search } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import complianceService, { ComplianceItem } from '@/services/complianceService';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';

const REGULATORY_BODIES = [
  { value: 'RBI', label: 'RBI' },
  { value: 'SEBI', label: 'SEBI' },
  { value: 'MCA', label: 'MCA' },
  { value: 'GST', label: 'GST' },
  { value: 'INCOME_TAX', label: 'Income Tax' },
  { value: 'EPFO', label: 'EPFO' },
  { value: 'ESIC', label: 'ESIC' },
  { value: 'STATE', label: 'State' },
  { value: 'OTHER', label: 'Other' },
];

const FREQUENCIES = [
  { value: 'DAILY', label: 'Daily' },
  { value: 'WEEKLY', label: 'Weekly' },
  { value: 'MONTHLY', label: 'Monthly' },
  { value: 'QUARTERLY', label: 'Quarterly' },
  { value: 'HALF_YEARLY', label: 'Half-Yearly' },
  { value: 'ANNUALLY', label: 'Annually' },
  { value: 'AS_REQUIRED', label: 'As Required' },
  { value: 'ONE_TIME', label: 'One Time' },
];

const PRIORITY_COLORS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  CRITICAL: 'destructive',
  HIGH: 'destructive',
  MEDIUM: 'default',
  LOW: 'outline',
};

export default function ComplianceItemList() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [items, setItems] = useState<ComplianceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [bodyFilter, setBodyFilter] = useState<string>('');
  const [frequencyFilter, setFrequencyFilter] = useState<string>('');
  const [total, setTotal] = useState(0);

  const organizationId = useRequiredActiveOrganizationId();

  useEffect(() => {
    loadItems();
  }, [bodyFilter, frequencyFilter]);

  const loadItems = async () => {
    try {
      setLoading(true);
      const response = await complianceService.listItems({
        organization_id: organizationId,
        regulatory_body: bodyFilter || undefined,
        frequency: frequencyFilter || undefined,
        active_only: true,
      });
      setItems(response.items);
      setTotal(response.total);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load compliance items',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to deactivate this item?')) return;

    try {
      await complianceService.deleteItem(id);
      toast({
        title: 'Success',
        description: 'Item deactivated successfully',
      });
      loadItems();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to deactivate item',
        variant: 'destructive',
      });
    }
  };

  const filteredItems = items.filter(
    (item) =>
      item.item_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.item_code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Compliance Items"
        subtitle="Manage compliance requirements and configurations"
        actions={
          <Button onClick={() => navigate('/admin/compliance/items/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Item
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row gap-4 justify-between">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search items..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Select value={bodyFilter} onValueChange={setBodyFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Bodies" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Bodies</SelectItem>
                  {REGULATORY_BODIES.map((body) => (
                    <SelectItem key={body.value} value={body.value}>
                      {body.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={frequencyFilter} onValueChange={setFrequencyFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Frequencies" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Frequencies</SelectItem>
                  {FREQUENCIES.map((freq) => (
                    <SelectItem key={freq.value} value={freq.value}>
                      {freq.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Regulator</TableHead>
                <TableHead>Frequency</TableHead>
                <TableHead>Due Day</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Form</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : filteredItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    No items found
                  </TableCell>
                </TableRow>
              ) : (
                filteredItems.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-mono">{item.item_code}</TableCell>
                    <TableCell className="font-medium">{item.item_name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{item.regulatory_body}</Badge>
                    </TableCell>
                    <TableCell>{item.frequency}</TableCell>
                    <TableCell>
                      {item.due_day ? `${item.due_day}${item.due_month ? ` (${item.due_month})` : ''}` : '-'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={PRIORITY_COLORS[item.priority]}>
                        {item.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>{item.form_name || '-'}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            navigate(`/admin/compliance/items/${item.id}/edit`)
                          }
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(item.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
