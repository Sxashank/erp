/**
 * PermissionGate — renders children only if the user has the given permission.
 * See CLAUDE.md §8.2.
 *
 * IMPORTANT: this is a UX convenience. Never trust the client for auth; the
 * backend must enforce every permission on the mutation itself.
 */

import {
  useHasAllPermissions,
  useHasAnyPermission,
  usePermission,
} from '@/hooks/usePermission';

interface OneProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  permission: string;
}

interface AnyProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  anyOf: readonly string[];
}

interface AllProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  allOf: readonly string[];
}

type Props = OneProps | AnyProps | AllProps;

export function PermissionGate(props: Props): JSX.Element | null {
  const { children, fallback = null } = props;
  // Always call the same hooks in the same order; short-circuit on props.
  const single = usePermission('permission' in props ? props.permission : '__noop__');
  const any = useHasAnyPermission('anyOf' in props ? props.anyOf : []);
  const all = useHasAllPermissions('allOf' in props ? props.allOf : []);

  let ok = false;
  if ('permission' in props) ok = single;
  else if ('anyOf' in props) ok = any;
  else if ('allOf' in props) ok = all;

  return <>{ok ? children : fallback}</>;
}
