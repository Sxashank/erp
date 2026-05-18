/**
 * Canonical common-components barrel. Prefer importing from here:
 *   import { PageHeader, DataTable, FormShell } from '@/components/common';
 *
 * See CLAUDE.md §5.2.
 */

export { AmountDisplay } from './AmountDisplay';
export { AmountInput, AmountField } from './AmountInput';
export type { AmountInputProps, AmountFieldProps } from './AmountInput';
export { ConfirmDialog } from './ConfirmDialog';
export type { ConfirmDialogProps } from './ConfirmDialog';
export { CustomerPicker } from './CustomerPicker';
export type { CustomerPickerProps } from './CustomerPicker';
export { DataTable } from './DataTable';
export type { Column, DataTableProps } from './DataTable';
export { DateDisplay } from './DateDisplay';
export { DetailGrid } from './DetailGrid';
export type { DetailField, DetailGridProps } from './DetailGrid';
export { DpdBadge } from './DpdBadge';
export { EmptyState } from './EmptyState';
export type { EmptyStateProps } from './EmptyState';
export { ErrorState } from './ErrorState';
export type { ErrorStateProps } from './ErrorState';
export { FilterBar } from './FilterBar';
export type { FilterBarProps } from './FilterBar';
export { FormShell, FormSection } from './FormShell';
export type { FormShellProps, FormSectionProps } from './FormShell';
export { InlineTabs } from './InlineTabs';
export type { InlineTabsProps, TabItem } from './InlineTabs';
export { MakerCheckerGate } from './MakerCheckerGate';
export { PageHeader } from './PageHeader';
export type { PageHeaderProps, BreadcrumbItem } from './PageHeader';
export { PercentageDisplay } from './PercentageDisplay';
export { PercentageInput } from './PercentageInput';
export type { PercentageInputProps } from './PercentageInput';
export { PermissionGate } from './PermissionGate';
export { RequireModuleAccess } from './RequireModuleAccess';
export { SkeletonTable } from './SkeletonTable';
export type { SkeletonTableProps } from './SkeletonTable';
export {
  StatusPill,
  ApplicationStatusBadge,
  AssetClassificationBadge,
  LoanAccountStatusBadge,
  EntityStatusBadge,
  RiskCategoryBadge,
} from './StatusPill';
