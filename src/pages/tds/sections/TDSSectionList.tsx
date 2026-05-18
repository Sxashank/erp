import { Edit, Plus, Trash2 } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DataTable, type Column } from '@/components/common/DataTable';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { PercentageDisplay } from '@/components/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useDeleteTDSSection,
  useTDSSections,
  type TDSSection,
} from '@/hooks/tax/useTaxation';

const RETURN_FORMS = [
  { value: 'all', label: 'All forms' },
  { value: '24Q', label: '24Q Salary' },
  { value: '26Q', label: '26Q Non-salary' },
  { value: '27Q', label: '27Q NRI' },
  { value: '27EQ', label: '27EQ TCS' },
];

export default function TDSSectionList() {
  const navigate = useNavigate();
  const [returnForm, setReturnForm] = useState('all');
  const sectionsQuery = useTDSSections({ pageSize: 100, includeInactive: true, returnForm });
  const deleteSection = useDeleteTDSSection();

  const columns = useMemo<Column<TDSSection>[]>(
    () => [
      { key: 'sectionCode', header: 'Section', sortable: true },
      { key: 'sectionName', header: 'Name', sortable: true },
      {
        key: 'rateIndividual',
        header: 'Individual',
        align: 'right',
        render: (section) => <PercentageDisplay value={section.rateIndividual} decimals={2} />,
      },
      {
        key: 'rateCompany',
        header: 'Company',
        align: 'right',
        render: (section) => <PercentageDisplay value={section.rateCompany} decimals={2} />,
      },
      {
        key: 'rateNoPan',
        header: 'No PAN',
        align: 'right',
        render: (section) => <PercentageDisplay value={section.rateNoPan} decimals={2} />,
      },
      {
        key: 'thresholdAnnual',
        header: 'Annual Threshold',
        align: 'right',
        render: (section) => <AmountDisplay amount={section.thresholdAnnual} compact />,
      },
      {
        key: 'returnForm',
        header: 'Return',
        render: (section) => section.returnForm ?? '-',
      },
      {
        key: 'isTcs',
        header: 'Type',
        render: (section) => (
          <Badge variant="outline">{section.isTcs ? 'TCS' : 'TDS'}</Badge>
        ),
      },
      {
        key: 'isActive',
        header: 'Status',
        render: (section) => (
          <Badge variant={section.isActive ? 'default' : 'secondary'}>
            {section.isActive ? 'Active' : 'Inactive'}
          </Badge>
        ),
      },
      {
        key: 'actions',
        header: 'Actions',
        align: 'right',
        render: (section) => (
          <div className="flex justify-end gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={(event) => {
                event.stopPropagation();
                navigate(`/admin/tds/sections/${section.id}/edit`);
              }}
              aria-label={`Edit ${section.sectionCode}`}
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              disabled={deleteSection.isPending}
              onClick={(event) => {
                event.stopPropagation();
                deleteSection.mutate(section.id);
              }}
              aria-label={`Delete ${section.sectionCode}`}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ),
      },
    ],
    [deleteSection, navigate],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="TDS/TCS Sections"
        subtitle="Manage effective-dated deduction and collection rules"
        actions={
          <Button onClick={() => navigate('/admin/tds/sections/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Section
          </Button>
        }
      />

      <FilterBar onClear={() => setReturnForm('all')}>
        <Select value={returnForm} onValueChange={setReturnForm}>
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Return form" />
          </SelectTrigger>
          <SelectContent>
            {RETURN_FORMS.map((form) => (
              <SelectItem key={form.value} value={form.value}>
                {form.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable
        data={sectionsQuery.data?.items ?? []}
        columns={columns}
        getRowId={(section) => section.id}
        isLoading={sectionsQuery.isLoading}
        error={sectionsQuery.error}
        onRetry={() => sectionsQuery.refetch()}
        emptyTitle="No TDS/TCS sections"
        emptySubtitle="Create sections before recording TDS or TCS entries."
      />
    </div>
  );
}
