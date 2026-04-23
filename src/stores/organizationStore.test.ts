/**
 * Unit tests for the organization store. See CLAUDE.md §3.4.
 */

import { describe, expect, it } from 'vitest';

import { useOrganizationStore } from './organizationStore';

function reset(): void {
  useOrganizationStore.setState({
    organizations: [],
    activeOrganizationId: null,
  });
}

describe('organizationStore', () => {
  it('setOrganizations picks the first as active when none is set', () => {
    reset();
    useOrganizationStore.getState().setOrganizations([
      { id: 'o1', code: 'HO', name: 'Head Office' },
      { id: 'o2', code: 'BR', name: 'Branch' },
    ]);
    expect(useOrganizationStore.getState().activeOrganizationId).toBe('o1');
  });

  it('setOrganizations preserves the active id if still valid', () => {
    reset();
    useOrganizationStore.setState({ activeOrganizationId: 'o2' });
    useOrganizationStore.getState().setOrganizations([
      { id: 'o1', code: 'HO', name: 'Head Office' },
      { id: 'o2', code: 'BR', name: 'Branch' },
    ]);
    expect(useOrganizationStore.getState().activeOrganizationId).toBe('o2');
  });

  it('setOrganizations resets active when it disappears from the list', () => {
    reset();
    useOrganizationStore.setState({ activeOrganizationId: 'gone' });
    useOrganizationStore.getState().setOrganizations([
      { id: 'o1', code: 'HO', name: 'Head Office' },
    ]);
    expect(useOrganizationStore.getState().activeOrganizationId).toBe('o1');
  });

  it('setActiveOrganization changes the active id', () => {
    reset();
    useOrganizationStore.getState().setOrganizations([
      { id: 'o1', code: 'HO', name: 'Head Office' },
      { id: 'o2', code: 'BR', name: 'Branch' },
    ]);
    useOrganizationStore.getState().setActiveOrganization('o2');
    expect(useOrganizationStore.getState().activeOrganizationId).toBe('o2');
  });

  it('clear wipes state', () => {
    reset();
    useOrganizationStore.getState().setOrganizations([
      { id: 'o1', code: 'HO', name: 'Head Office' },
    ]);
    useOrganizationStore.getState().clear();
    expect(useOrganizationStore.getState().organizations).toHaveLength(0);
    expect(useOrganizationStore.getState().activeOrganizationId).toBeNull();
  });
});
