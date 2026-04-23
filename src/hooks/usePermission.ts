/**
 * Permission hooks. Permissions are `<resource>.<action>` strings stored in
 * a Set on the auth store. See CLAUDE.md §8.2.
 *
 * Example:
 *   const canPost = usePermission('voucher.post');
 *   if (!canPost) return null;
 */

import { useAuthStore } from '@/stores/authStore';

export function usePermission(perm: string): boolean {
  return useAuthStore((s) => s.permissions.has(perm));
}

export function useHasAnyPermission(perms: readonly string[]): boolean {
  return useAuthStore((s) => perms.some((p) => s.permissions.has(p)));
}

export function useHasAllPermissions(perms: readonly string[]): boolean {
  return useAuthStore((s) => perms.every((p) => s.permissions.has(p)));
}
