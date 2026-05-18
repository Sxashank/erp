/**
 * Legacy dashboard entrypoint.
 *
 * The scheme portal workbench replaces the old retail dashboard. Keep this
 * file as a thin compatibility export so any lingering imports resolve to
 * the borrower workbench instead of compiling stale retail UI.
 */

export { default } from './PortalWorkbench';
