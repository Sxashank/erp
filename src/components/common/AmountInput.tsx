/**
 * Canonical AmountInput home. Re-exports the implementation currently in the
 * lending/ folder; follow-up refactor (Stage 7) will move the implementation
 * here and have the lending/ path re-export. See CLAUDE.md §5.2, §5.8.
 */

export { AmountInput, AmountField } from '@/components/lending/common/AmountInput';
export type { AmountInputProps, AmountFieldProps } from '@/components/lending/common/AmountInput';
