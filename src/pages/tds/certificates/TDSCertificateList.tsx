import { Eye, Plus } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DataTable } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { ItcResolutionStatusBadge } from '@/components/gst/GstnStatusBadge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useFinancialYears, useTDSCertificates, type TDSCertificateInfo } from '@/hooks/tax/useTaxation';
import { useActiveOrganizationId } from '@/stores/organizationStore';
import { getFinancialYearValue } from '@/utils/financialYears';

export default function TDSCertificateList() {
  const navigate = useNavigate();
  const activeOrganizationId = useActiveOrganizationId();
  const [financialYear, setFinancialYear] = useState('');
  const [quarter, setQuarter] = useState('all');
  const financialYearsQuery = useFinancialYears();
  const certificatesQuery = useTDSCertificates(
    financialYear || undefined,
    quarter === 'all' ? undefined : quarter,
  );

  const columns = useMemo(
    () => [
      { key: 'certificateNumber', header: 'Certificate No.', sortable: true },
      { key: 'deducteeName', header: 'Deductee', sortable: true },
      { key: 'deducteePan', header: 'PAN' },
      { key: 'tdsSectionCode', header: 'Section' },
      {
        key: 'totalTdsDeducted',
        header: 'TDS Deducted',
        align: 'right' as const,
        render: (item: TDSCertificateInfo) => <AmountDisplay amount={item.totalTdsDeducted} />,
      },
      {
        key: 'certificateDate',
        header: 'Certificate Date',
        render: (item: TDSCertificateInfo) => item.certificateDate ? <DateDisplay date={item.certificateDate} /> : '—',
      },
      {
        key: 'legalStatus',
        header: 'Legal Status',
        render: (item: TDSCertificateInfo) => <ItcResolutionStatusBadge status={item.legalStatus} />,
      },
      {
        key: 'actions',
        header: 'Actions',
        align: 'right' as const,
        render: (item: TDSCertificateInfo) => (
          <Button type="button" variant="ghost" size="icon" onClick={(event) => { event.stopPropagation(); navigate(`/admin/tds/certificates/${item.certificateNumber}`); }}>
            <Eye className="h-4 w-4" />
          </Button>
        ),
      },
    ],
    [navigate],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="TDS Certificates"
        subtitle="Generate working summaries and track certificate evidence for deductees"
        actions={<Button onClick={() => navigate('/admin/tds/certificates/generate')}><Plus className="mr-2 h-4 w-4" />Generate Certificates</Button>}
      />

      <FilterBar onClear={() => { setFinancialYear(''); setQuarter('all'); }}>
        <Select value={financialYear} onValueChange={setFinancialYear}>
          <SelectTrigger className="w-[220px]"><SelectValue placeholder="Select financial year" /></SelectTrigger>
          <SelectContent>
            {(financialYearsQuery.data?.items ?? []).map((year) => (
              <SelectItem key={year.id} value={getFinancialYearValue(year)}>
                {year.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={quarter} onValueChange={setQuarter}>
          <SelectTrigger className="w-[140px]"><SelectValue placeholder="Quarter" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All quarters</SelectItem>
            <SelectItem value="Q1">Q1</SelectItem>
            <SelectItem value="Q2">Q2</SelectItem>
            <SelectItem value="Q3">Q3</SelectItem>
            <SelectItem value="Q4">Q4</SelectItem>
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable
        data={financialYear ? certificatesQuery.data ?? [] : []}
        columns={columns}
        getRowId={(item) => item.certificateNumber}
        isLoading={certificatesQuery.isLoading}
        error={certificatesQuery.error}
        onRetry={() => certificatesQuery.refetch()}
        emptyTitle="No certificates"
        emptySubtitle={financialYear ? 'Generate certificates after challans are paid and return evidence is ready.' : 'Select a financial year to view certificates.'}
        onRowClick={(item) => navigate(`/admin/tds/certificates/${item.certificateNumber}`)}
      />
    </div>
  );
}
