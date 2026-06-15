import { execFileSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import path from 'node:path';

import type { Page } from '@playwright/test';

import { expect, test } from '../fixtures/test';

const env =
  (globalThis as { process?: { cwd?: () => string; env?: Record<string, string | undefined> } })
    .process ?? {};
const API_BASE = env.env?.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ESS_MOBILE = env.env?.ESS_DEMO_MOBILE || '9876543210';
const LIVE_BACKEND_ENABLED = env.env?.PLAYWRIGHT_LIVE_BACKEND === '1';
const proofDir = path.join(env.cwd?.() ?? '.', 'test-results', 'ess-hrms-proof');

function readLatestOtp() {
  return execFileSync(
    'bash',
    [
      '-lc',
      `cd backend && .venv/bin/python - <<'PY'
import asyncio
from sqlalchemy import text
from app.database import async_session_factory

async def main():
    async with async_session_factory() as session:
        result = await session.execute(
            text("select otp_code from ess_otp where mobile=:mobile order by created_at desc limit 1"),
            {"mobile": "${ESS_MOBILE}"},
        )
        print(result.scalar_one())

asyncio.run(main())
PY`,
    ],
    { encoding: 'utf8' },
  ).trim();
}

async function screenshot(page: Page, name: string) {
  await page.screenshot({
    path: path.join(proofDir, `${name}.png`),
    fullPage: true,
  });
}

test.describe('ESS + HRMS live proof', () => {
  test.skip(!LIVE_BACKEND_ENABLED, 'Set PLAYWRIGHT_LIVE_BACKEND=1 to run live ESS proof.');
  test.skip(({ browserName }) => browserName !== 'chromium', 'Proof screenshots use Chromium only.');

  test('employee can log in and open every active ESS workflow', async ({ page, request }) => {
    mkdirSync(proofDir, { recursive: true });

    await page.goto('/ess/login', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Employee Self Service' })).toBeVisible();
    await page.getByLabel('Mobile Number').fill(ESS_MOBILE);
    await page.getByRole('button', { name: 'Send OTP' }).click();

    const sendOtp = await request.post(`${API_BASE}/ess/auth/send-otp`, {
      data: { mobile: ESS_MOBILE },
    });
    expect(sendOtp.ok(), await sendOtp.text()).toBeTruthy();
    const otp = readLatestOtp();
    await page.getByLabel('One-Time Password').fill(otp);
    await page.getByRole('button', { name: 'Verify & Login' }).click();
    await page.waitForURL('**/ess/dashboard', { timeout: 20_000 });
    await expect(page.getByText('Welcome,', { exact: false })).toBeVisible();
    await screenshot(page, '01-dashboard');

    const pages = [
      { path: '/ess/profile', title: 'My Profile', shot: '02-profile' },
      { path: '/ess/attendance', title: 'Attendance', shot: '03-attendance' },
      { path: '/ess/leave', title: 'Leave', shot: '04-leave' },
      { path: '/ess/payslips', title: 'Payslips', shot: '05-payslips' },
      { path: '/ess/reimbursements', title: 'Reimbursements', shot: '06-reimbursements' },
      { path: '/ess/it-declaration', title: 'IT Declaration', shot: '07-it-declaration' },
      { path: '/ess/assets', title: 'Assigned Assets', shot: '08-assets' },
      { path: '/ess/training', title: 'Training & Learning', shot: '09-training' },
      { path: '/ess/goals', title: 'Goals', shot: '10-goals' },
      { path: '/ess/self-appraisal', title: 'Self Appraisal', shot: '11-self-appraisal' },
      { path: '/ess/helpdesk', title: 'Helpdesk', shot: '12-helpdesk' },
    ];

    for (const item of pages) {
      await page.goto(item.path, { waitUntil: 'domcontentloaded' });
      await expect(page.getByRole('heading', { name: item.title, exact: true })).toBeVisible();
      await screenshot(page, item.shot);
    }

    await page.goto('/ess/leave', { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: 'Apply Leave' }).click();
    await expect(page.getByRole('heading', { name: 'Apply for leave' })).toBeVisible();
    await screenshot(page, '13-leave-apply-dialog');

    await page.goto('/ess/reimbursements', { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: 'New Claim' }).click();
    await expect(page.getByText('Create Reimbursement Claim')).toBeVisible();
    await screenshot(page, '14-reimbursement-new-claim-dialog');

    await page.goto('/ess/helpdesk', { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: 'New Ticket' }).click();
    await expect(page.getByText('Create Support Ticket')).toBeVisible();
    await screenshot(page, '15-helpdesk-new-ticket-dialog');
  });
});
