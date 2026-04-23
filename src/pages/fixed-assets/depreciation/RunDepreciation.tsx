import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Play } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { fixedAssetsApi, organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

export function RunDepreciation() {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [runLoading, setRunLoading] = useState(false);
  const [runPeriod, setRunPeriod] = useState('');
  const [runRemarks, setRunRemarks] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const handleRunDepreciation = async () => {
    if (!selectedOrgId || !runPeriod) return;
    try {
      setRunLoading(true);
      setError(null);
      await fixedAssetsApi.runDepreciation({
        organization_id: selectedOrgId,
        depreciation_period: runPeriod,
        remarks: runRemarks || undefined,
      });
      navigate('/admin/fixed-assets/depreciation');
    } catch (error: any) {
      console.error('Failed to run depreciation:', error);
      setError(error.response?.data?.detail || 'Failed to run depreciation');
    } finally {
      setRunLoading(false);
    }
  };

  const formatPeriod = (period: string) => {
    const [year, month] = period.split('-');
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${monthNames[parseInt(month) - 1]} ${year}`;
  };

  const getPeriodOptions = () => {
    const options = [];
    const now = new Date();
    for (let i = 0; i < 12; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const label = formatPeriod(value);
      options.push({ value, label });
    }
    return options;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Run Depreciation"
        subtitle="Calculate and record depreciation for all active assets"
        breadcrumbs={[
          { label: 'Depreciation', to: '/admin/fixed-assets/depreciation' },
          { label: 'Run' },
        ]}
      />

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Depreciation Parameters</CardTitle>
          <CardDescription>
            Select the period and organization to process monthly depreciation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="organization">Organization</Label>
            <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
              <SelectTrigger>
                <SelectValue placeholder="Select organization" />
              </SelectTrigger>
              <SelectContent>
                {organizations.map((org) => (
                  <SelectItem key={org.id} value={org.id}>
                    {org.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="period">Depreciation Period</Label>
            <Select value={runPeriod} onValueChange={setRunPeriod}>
              <SelectTrigger>
                <SelectValue placeholder="Select period" />
              </SelectTrigger>
              <SelectContent>
                {getPeriodOptions().map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="remarks">Remarks (Optional)</Label>
            <Textarea
              id="remarks"
              value={runRemarks}
              onChange={(e) => setRunRemarks(e.target.value)}
              placeholder="Add any notes for this depreciation run"
              rows={3}
            />
          </div>

          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 rounded-md">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-4 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/admin/fixed-assets/depreciation')}
            >
              Cancel
            </Button>
            <Button onClick={handleRunDepreciation} disabled={!runPeriod || !selectedOrgId || runLoading}>
              <Play className="mr-2 h-4 w-4" />
              {runLoading ? 'Processing...' : 'Run Depreciation'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
