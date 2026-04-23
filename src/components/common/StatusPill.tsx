/**
 * Canonical StatusPill home. Re-exports from the lending/ StatusBadge until
 * the implementation migrates. See CLAUDE.md §5.8.
 */

export {
  StatusBadge as StatusPill,
  ApplicationStatusBadge,
  AssetClassificationBadge,
  LoanAccountStatusBadge,
  EntityStatusBadge,
  RiskCategoryBadge,
} from '@/components/lending/common/StatusBadge';
