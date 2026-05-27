import { expect, test } from '../fixtures/test';

const templateId = '11111111-1111-4111-8111-111111111111';
const versionId = '22222222-2222-4222-8222-222222222222';
const entityId = '33333333-3333-4333-8333-333333333333';

test.describe('document studio', () => {
  test('renders template, filing, and package workbench with screenshots', async ({
    authedPage: page,
    consoleGate,
  }, testInfo) => {
    consoleGate.allowError(/401|Unauthorized/i);
    consoleGate.allowStatus(401);
    consoleGate.allowStatus(404);

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        json: {
          id: '22222222-2222-4222-8222-222222222222',
          username: 'admin',
          email: 'admin@example.test',
          fullName: 'Admin User',
          organizationId: '11111111-1111-1111-1111-111111111111',
          defaultUnitId: null,
          mfaEnabled: false,
          roles: [{ id: 'role-1', code: 'SUPER_ADMIN', name: 'Super Admin' }],
          permissions: [
            'DMS_DOCUMENT_VIEW',
            'DMS_DOCUMENT_UPLOAD',
            'DMS_DOCUMENT_UPDATE',
            'DMS_FOLDER_VIEW',
            'DMS_FOLDER_CREATE',
          ],
        },
      });
    });

    await page.route('**/api/v1/auth/refresh', async (route) => {
      await route.fulfill({
        json: {
          accessToken: 'playwright-access-token',
          refreshToken: 'playwright-refresh-token',
          tokenType: 'bearer',
          expiresIn: 900,
        },
      });
    });

    await page.route('**/api/v1/organizations**', async (route) => {
      await route.fulfill({
        json: {
          items: [
            {
              id: '11111111-1111-1111-1111-111111111111',
              code: 'SMFC',
              name: 'SMFC Ltd',
            },
          ],
          total: 1,
        },
      });
    });

    await page.route('**/api/v1/document-studio/templates**', async (route) => {
      if (route.request().method() !== 'GET') return route.fallback();
      if (!new URL(route.request().url()).pathname.endsWith('/document-studio/templates')) {
        return route.fallback();
      }
      await route.fulfill({
        json: {
          items: [
            {
              id: templateId,
              module: 'LENDING',
              documentType: 'SANCTION_LETTER',
              code: 'SANCTION_LETTER_DEFAULT',
              name: 'Default Sanction Letter',
              description: 'Governed sanction communication',
              locale: 'en',
              channel: 'PDF',
              priority: 100,
              selectionRules: {},
              isSystem: true,
              versions: [
                {
                  id: versionId,
                  templateId,
                  versionNumber: 1,
                  status: 'PUBLISHED',
                  format: 'HTML',
                  body: 'Dear {{ entity.legalName }}',
                  header: '{{ organization.name }}',
                  footer: 'Authorised Signatory',
                  styleConfig: {},
                  variableSchema: {},
                  requiredVariables: ['entity.legalName'],
                  lockedBlocks: [],
                  publishedAt: '2026-05-26T00:00:00Z',
                },
              ],
            },
          ],
          total: 1,
        },
      });
    });

    await page.route(`**/api/v1/document-studio/templates/${templateId}`, async (route) => {
      await route.fulfill({
        json: {
          id: templateId,
          module: 'LENDING',
          documentType: 'SANCTION_LETTER',
          code: 'SANCTION_LETTER_DEFAULT',
          name: 'Default Sanction Letter',
          description: 'Governed sanction communication',
          locale: 'en',
          channel: 'PDF',
          priority: 100,
          selectionRules: {},
          isSystem: true,
          versions: [
            {
              id: versionId,
              templateId,
              versionNumber: 1,
              status: 'PUBLISHED',
              format: 'HTML',
              body: 'Dear {{ entity.legalName }}',
              header: '{{ organization.name }}',
              footer: 'Authorised Signatory',
              styleConfig: {},
              variableSchema: {},
              requiredVariables: ['entity.legalName'],
              lockedBlocks: [],
              publishedAt: '2026-05-26T00:00:00Z',
            },
          ],
        },
      });
    });

    await page.route('**/api/v1/document-studio/variables**', async (route) => {
      await route.fulfill({
        json: {
          module: 'LENDING',
          documentType: 'SANCTION_LETTER',
          items: [
            {
              key: 'entity.legalName',
              label: 'Legal Name',
              description: 'Borrower legal name',
              required: true,
            },
            {
              key: 'sanction.sanctionedAmount',
              label: 'Sanction Amount',
              description: 'Approved amount',
              formatter: 'amount',
            },
          ],
        },
      });
    });

    await page.route('**/api/v1/document-studio/preview', async (route) => {
      await route.fulfill({
        json: {
          renderedHtml:
            'SMFC Ltd\nDear Example Borrower Pvt Ltd,\nSanction SAN/2026/0001 is ready.',
          missingVariables: [],
        },
      });
    });

    await page.route('**/api/v1/dms/filing-rules**', async (route) => {
      await route.fulfill({
        json: [
          {
            id: '44444444-4444-4444-8444-444444444444',
            module: 'LENDING',
            documentType: 'SANCTION_LETTER',
            entityType: 'sanction',
            pathTemplate:
              '/Entities/{{ entity.entityCode }}/Loans/{{ loanAccount.accountNumber }}/Sanction & Agreements',
            accessLevel: 'organization',
            portalVisible: true,
            defaultTags: ['lending', 'sanction'],
            priority: 100,
            isSystem: true,
          },
          {
            id: '55555555-5555-4555-8555-555555555555',
            module: 'PAYROLL',
            documentType: 'PAYSLIP',
            entityType: 'employee',
            pathTemplate: '/Employees/{{ employee.employeeCode }}/Payroll',
            accessLevel: 'organization',
            portalVisible: false,
            defaultTags: ['payroll'],
            priority: 100,
            isSystem: true,
          },
        ],
      });
    });

    await page.route('**/api/v1/documents/packages**', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          json: {
            id: '66666666-6666-4666-8666-666666666666',
            packageNumber: 'PKG/SANCTION-PACKAGE/20260526/0001',
            packageType: 'SANCTION_PACKAGE',
            name: 'Sample Sanction Package',
            status: 'DRAFT',
            entityType: 'sanction',
            entityId,
            manifest: { source: 'DOCUMENT_STUDIO' },
          },
        });
        return;
      }
      await route.fulfill({
        json: {
          items: [
            {
              id: '66666666-6666-4666-8666-666666666666',
              packageNumber: 'PKG/SANCTION-PACKAGE/20260526/0001',
              packageType: 'SANCTION_PACKAGE',
              name: 'Sample Sanction Package',
              status: 'DRAFT',
              entityType: 'sanction',
              entityId,
              manifest: { source: 'DOCUMENT_STUDIO' },
            },
          ],
          total: 1,
        },
      });
    });

    await page.goto('/admin/dms/document-studio');
    await expect(page.getByRole('heading', { name: 'Document Studio' })).toBeVisible();
    await expect(page.getByText('Default Sanction Letter')).toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath('document-studio-templates-desktop.png'),
      fullPage: true,
    });

    await page.getByText('Default Sanction Letter').click();
    await expect(page.getByRole('heading', { name: 'Default Sanction Letter' })).toBeVisible();
    await page.getByRole('button', { name: /render sample/i }).click();
    await expect(
      page.frameLocator('iframe[title="Document preview"]').getByText('Example Borrower Pvt Ltd'),
    ).toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath('document-studio-template-detail-desktop.png'),
      fullPage: true,
    });

    await page.goto('/admin/dms/document-studio/filing-rules');
    await expect(page.getByText('Sanction & Agreements')).toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath('document-studio-filing-desktop.png'),
      fullPage: true,
    });

    await page.goto('/admin/dms/document-studio/packages');
    await expect(page.getByText('Sample Sanction Package')).toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath('document-studio-packages-desktop.png'),
      fullPage: true,
    });
  });
});
