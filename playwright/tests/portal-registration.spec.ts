import { expect, test } from '@playwright/test';

test.describe('Borrower portal registration', () => {
  test('renders both registration paths and swaps the form fields', async ({ page }) => {
    await page.goto('/portal/register');

    await expect(page.getByRole('heading', { name: 'Register your organisation' })).toBeVisible();
    await expect(page.getByText('Registration path')).toBeVisible();

    await expect(page.getByPlaceholder('L12345AB6789CDE123456')).toBeVisible();
    await expect(page.getByPlaceholder('SMFC/LA/2026/00001')).toHaveCount(0);

    await page.getByLabel('Existing loan').click();
    await expect(page.getByPlaceholder('SMFC/LA/2026/00001')).toBeVisible();
    await expect(page.getByPlaceholder('2500000.00')).toBeVisible();
    await expect(page.getByPlaceholder('L12345AB6789CDE123456')).toHaveCount(0);

    await page.getByLabel('Organisation identifier').click();
    await expect(page.getByPlaceholder('L12345AB6789CDE123456')).toBeVisible();
  });
});
