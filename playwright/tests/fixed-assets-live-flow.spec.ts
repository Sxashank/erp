import { execFile } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';

import { expect, test } from '../fixtures/test';

const execFileAsync = promisify(execFile);
const LIVE_BACKEND_ENABLED = process.env.PLAYWRIGHT_LIVE_BACKEND === '1';
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5176';
const API_BASE = process.env.PLAYWRIGHT_API_BASE ?? 'http://localhost:8001/api/v1';

async function readSummary(outputDir: string) {
  const files = await fs.readdir(outputDir);
  const summaries = files
    .filter((file: string) => file.startsWith('summary-') && file.endsWith('.json'))
    .sort();
  if (summaries.length === 0) {
    throw new Error(`No live-flow summary file found in ${outputDir}`);
  }
  const summaryPath = path.join(outputDir, summaries[summaries.length - 1]);
  const summary = JSON.parse(await fs.readFile(summaryPath, 'utf8')) as Record<string, unknown>;
  return { summaryPath, summary };
}

test.describe('Fixed-assets live flow', () => {
  test.skip(!LIVE_BACKEND_ENABLED, 'Requires a live backend and real seeded data');
  test.skip(({ browserName }) => browserName !== 'chromium', 'Runs only in the desktop Chromium project');

  test('completes the operational-core flow with live data', async (_fixtures, testInfo) => {
    test.setTimeout(6 * 60 * 1000);

    const outputDir = path.join(testInfo.outputDir, 'fixed-assets-live-flow');
    await fs.mkdir(outputDir, { recursive: true });

    const stdoutPath = path.join(outputDir, 'runner-stdout.log');
    const stderrPath = path.join(outputDir, 'runner-stderr.log');

    const { stdout, stderr } = await execFileAsync(
      'pnpm',
      ['exec', 'node', 'scripts/fixed-assets-live-flow.mjs'],
      {
        cwd: process.cwd(),
        env: {
          ...process.env,
          PLAYWRIGHT_BASE_URL: BASE_URL,
          PLAYWRIGHT_API_BASE: API_BASE,
          FIXED_ASSETS_LIVE_FLOW_OUTPUT_DIR: outputDir,
        },
        maxBuffer: 10 * 1024 * 1024,
      },
    );

    await fs.writeFile(stdoutPath, stdout, 'utf8');
    await fs.writeFile(stderrPath, stderr, 'utf8');
    await testInfo.attach('fixed-assets-live-flow-stdout', {
      path: stdoutPath,
      contentType: 'text/plain',
    });
    await testInfo.attach('fixed-assets-live-flow-stderr', {
      path: stderrPath,
      contentType: 'text/plain',
    });

    const { summaryPath, summary } = await readSummary(outputDir);
    await testInfo.attach('fixed-assets-live-flow-summary', {
      path: summaryPath,
      contentType: 'application/json',
    });

    expect(summary.error).toBeNull();
    expect(summary.consoleErrors).toEqual([]);
    expect(summary.failedResponses).toEqual([]);

    expect(summary.categoryCode).toMatch(/^UATFA/);
    expect(summary.assetId).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );

    const records = summary.records as Record<string, Record<string, unknown> | null>;
    const category = records.category ?? {};
    const asset = records.asset ?? {};
    const depreciationRun = records.depreciationRun ?? {};
    const verificationSchedule = records.verificationSchedule ?? {};
    const disposal = records.disposal ?? {};

    expect(category.categoryCode).toBe(summary.categoryCode);
    expect(asset.assetName).toBe(summary.assetName);
    expect(asset.status).toBe('DISPOSED');
    expect(asset.disposalRemarks).toBe(`${summary.runLabel} disposal`);
    expect(depreciationRun.depreciationPeriod).toBe(summary.depreciationPeriod);
    expect(depreciationRun.status).toBe('POSTED');
    expect(verificationSchedule.scheduleName).toBe(summary.scheduleName);
    expect(verificationSchedule.status).toBe('COMPLETED');
    expect(disposal.status).toBe('COMPLETED');

    const downloads = summary.downloads as Record<string, string>;
    await expect(fs.stat(downloads.assetRegisterPath)).resolves.toBeTruthy();
    await expect(fs.stat(downloads.depreciationPath)).resolves.toBeTruthy();

    const screenshots = summary.screenshots as Record<string, string>;
    await expect(fs.stat(screenshots.categories)).resolves.toBeTruthy();
    await expect(fs.stat(screenshots.assetDraft)).resolves.toBeTruthy();
    await expect(fs.stat(screenshots.depreciationRun)).resolves.toBeTruthy();
    await expect(fs.stat(screenshots.verification)).resolves.toBeTruthy();
    await expect(fs.stat(screenshots.disposal)).resolves.toBeTruthy();
  });
});
