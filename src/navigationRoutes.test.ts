import fs from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

const SRC_DIR = path.resolve(process.cwd(), 'src');
const APP_FILE = path.join(SRC_DIR, 'App.tsx');

function extractRoutePaths(segment: string, prefix = '') {
  const routePaths: string[] = [];
  const routePathPattern = /<Route\s+[^>]*path=(?:"([^"]+)"|'([^']+)')/g;
  let match: RegExpExecArray | null;

  while ((match = routePathPattern.exec(segment))) {
    const routePath = match[1] ?? match[2];
    if (!routePath || routePath === '*') continue;
    routePaths.push(routePath.startsWith('/') ? routePath : `${prefix}/${routePath}`);
  }

  return routePaths.map((routePath) => routePath.replace(/\/+/g, '/'));
}

function routePatternToRegex(routePath: string) {
  const parts = routePath
    .split('/')
    .filter(Boolean)
    .map((part) => (part.startsWith(':') ? '[^/]+' : part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));

  return new RegExp(`^/${parts.join('/')}/?$`);
}

function normalizeNavigationTarget(rawTarget: string) {
  const withDynamicSegments = rawTarget.replace(/\$\{[^}]+}/g, ':param');
  const adminIndex = withDynamicSegments.indexOf('/admin/');
  const portalIndex = withDynamicSegments.search(/\/(portal|vendor|ess)\//);
  const target =
    adminIndex > 0
      ? withDynamicSegments.slice(adminIndex)
      : portalIndex > 0 && !withDynamicSegments.startsWith('/admin/')
        ? withDynamicSegments.slice(portalIndex)
        : withDynamicSegments;

  return target.split(/[?#]/)[0].replace(/\/+/g, '/');
}

function listSourceFiles(dir: string): string[] {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    if (['node_modules', '.git', 'dist', 'build', 'coverage'].includes(entry.name)) {
      return [];
    }

    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) return listSourceFiles(fullPath);
    return /\.(tsx?|jsx?)$/.test(entry.name) ? [fullPath] : [];
  });
}

function extractRegisteredRoutes() {
  const appSource = fs.readFileSync(APP_FILE, 'utf8');
  const protectedRoutesStart = appSource.indexOf('{/* Protected admin routes');
  const essRoutesStart = appSource.indexOf('{/* ESS Portal Routes');
  const portalRoutesStart = appSource.indexOf('{/* Scheme Portal Routes');
  const vendorRoutesStart = appSource.indexOf('{/* Vendor Portal Routes');
  const defaultRoutesStart = appSource.indexOf('{/* Default redirect');

  return [
    ...extractRoutePaths(appSource.slice(0, protectedRoutesStart)),
    ...extractRoutePaths(appSource.slice(protectedRoutesStart, essRoutesStart), '/admin'),
    ...extractRoutePaths(appSource.slice(essRoutesStart, portalRoutesStart), '/ess'),
    ...extractRoutePaths(appSource.slice(portalRoutesStart, vendorRoutesStart), '/portal'),
    ...extractRoutePaths(appSource.slice(vendorRoutesStart, defaultRoutesStart), '/vendor'),
  ];
}

describe('navigation route registry', () => {
  it('keeps static in-app navigation targets registered in App routes', () => {
    const registeredRoutePatterns = [...new Set(extractRegisteredRoutes())].map((routePath) =>
      routePatternToRegex(routePath),
    );
    const sourceFiles = listSourceFiles(SRC_DIR).filter((filePath) => filePath !== APP_FILE);
    const navigationTargetPatterns = [
      /(?:to|href)\s*=\s*["'](\/[A-Za-z0-9_./:#?=&-]+)["']/g,
      /navigate\(\s*["'](\/[A-Za-z0-9_./:#?=&-]+)["']/g,
      /(?:href|path)\s*:\s*["'](\/[A-Za-z0-9_./:#?=&-]+)["']/g,
      /(?:to|href)\s*=\s*\{`([^`]*\/(?:admin|portal|vendor|ess)\/[^`]*)`}/g,
      /navigate\(\s*`([^`]*\/(?:admin|portal|vendor|ess)\/[^`]*)`/g,
    ];

    const missingTargets = sourceFiles.flatMap((filePath) => {
      const source = fs.readFileSync(filePath, 'utf8');
      const misses: string[] = [];

      for (const pattern of navigationTargetPatterns) {
        let match: RegExpExecArray | null;

        while ((match = pattern.exec(source))) {
          const rawTarget = match[1];
          if (!rawTarget || rawTarget.startsWith('/api')) continue;

          const target = normalizeNavigationTarget(rawTarget);
          const isInAppTarget = [
            '/admin',
            '/portal',
            '/vendor',
            '/ess',
            '/login',
            '/forgot-password',
            '/reset-password',
          ].some((prefix) => target === prefix || target.startsWith(`${prefix}/`));

          if (!isInAppTarget) continue;
          if (registeredRoutePatterns.some((routePattern) => routePattern.test(target))) continue;

          const line = source.slice(0, match.index).split('\n').length;
          misses.push(`${path.relative(process.cwd(), filePath)}:${line} -> ${target}`);
        }
      }

      return misses;
    });

    expect(missingTargets).toEqual([]);
  });
});
