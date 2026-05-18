# Loan Module Contract Audit And Other Modules Report

Date: 2026-05-14

## Scope

- Lending/loan module reviewed across frontend pages, hooks, services, schemas, and relevant backend lending schemas/endpoints.
- Other modules were reviewed in read-only mode only, except one admin portal entity-filter call that had to follow the lending entity hook contract.
- External integrations remain out of scope for the current manual release posture.

## Contract Standard Applied

- Backend Python models/schemas keep snake_case internally.
- Frontend-facing JSON must be camelCase through Pydantic `CamelSchema` and FastAPI alias serialization.
- Frontend DTOs, form schemas, and page field names must be camelCase.
- Pages must not patch API drift with mixed snake/camel fallback types or inline DTO mapping.
- Query-string parameter names may remain backend-native at the service/hook boundary only.

## Lending Module Work Completed In This Pass

### Treasury Source-Lender And Borrowing Contracts

- Borrowing create/edit form now uses camelCase RHF/zod fields end to end.
- Lender create/edit form now uses camelCase RHF/zod fields end to end.
- Frontend treasury service contracts now expose camelCase lender and borrowing DTOs.
- Backend lender create/update/response schemas now inherit from `CamelSchema`.
- Backend lender create/get/update routes now explicitly serialize by alias.
- Treasury lender/borrowing pages no longer use `console.error` in render-tested code paths.
- Type validation passed with `pnpm exec tsc --noEmit --pretty false`.

### UAT-Blocking Console Failures Removed

- Removed `console.error` usage from lending pages/components so Playwright console-error checks do not fail on handled API failures.
- Remaining UAT readiness must still validate API/network failures screen by screen.

### LOS Entity Contracts

- Entity list/detail/form/tabs now consume camelCase DTOs consistently.
- Entity contacts, addresses, bank accounts, financials, and KYC tab display logic no longer reads snake_case response fields.
- Entity nested create/update/delete service methods now call the actual backend route shapes instead of nested workaround URLs.
- Backend entity/contact/address/bank/financial schemas now inherit from `CamelSchema` and serialize aliases.
- Backend contact create/update now maps the UI display `name` into normalized `first_name`/`last_name` model fields.
- Backend entity financial schemas now match the ORM fields instead of exposing non-existent accounting field names.
- Lending common `EntityCard` now uses the same camelCase entity contract as pages.
- Manual KYC document upload, manual verification/rejection, and delete endpoints now exist for entity KYC; no external KYC/GST/bank integration is invoked.
- Entity KYC request/response schemas now match ORM fields and serialize camelCase to the UI.

### LOS Application Contracts

- Application create/update backend schemas now inherit from `CamelSchema`; create sets `organization_id` server-side from the authenticated user instead of requiring the frontend to send it.
- Application create/update/submit/move-to-appraisal/detail routes now explicitly serialize aliases.
- Wizard navigation now passes the actual accumulated wizard data to submit/save handlers instead of using no-argument callback casts.
- Application wizard step data, zod schemas, request payloads, and UI review fields now use camelCase names.
- Application draft save now uses the real create/update endpoints rather than non-existent `/draft` routes.
- Application list filters now use camelCase in React and translate to backend query-string names only at the hook/service boundary.
- Application status/stage badges now cover the backend `LEAD` and `CLOSED` stage values.
- Application document schemas now align to actual ORM fields (`documentCode`, `fileSizeBytes`, `fileMimeType`, `status`) and serialize camelCase.
- Application milestone schemas now align to actual ORM fields (`milestoneName`, `expectedDate`, `actualDate`) and serialize camelCase.
- Manual application document verification now updates the actual `status` field; manual milestone completion now updates `actualDate`.
- Application document delete endpoint now exists for the frontend route shape; no external DMS integration was added.
- Application fee schemas now align to actual ORM fields (`feeCode`, `approvedAmount`, GST split amounts, collection status) and serialize camelCase.
- Manual fee collection now updates the real `status`, `collectionDate`, and `collectionReference` fields instead of non-existent collected fields.
- Technical appraisal schemas now align to actual ORM fields and create missing manual references/appraiser assignment server-side.
- Financial analysis schemas now align to actual ORM fields and create missing manual references/analyst assignment server-side.
- Application fee, technical appraisal, and financial appraisal endpoints now explicitly serialize aliases.

### LOS Product Contracts

- Product create/update/detail backend schemas now inherit from `CamelSchema`; create sets `organization_id` server-side from the authenticated user.
- Product create/get/update/detail routes now explicitly serialize aliases.
- Product list flattening now uses actual ORM fields (`base_rate.current_rate`, `default_spread_bps`, `is_active_for_new_loans`) instead of non-existent helper fields.
- Product list/detail hooks and pages now use camelCase DTO fields and keep backend query names at the hook boundary only.
- Product fee schemas now align to actual ORM fields including override calculation/rate/amount/min/max fields and serialize camelCase.
- Product document checklist schemas now align to actual ORM fields including applicability, expiry, file rules, and verification instructions.
- Product fee master, product fee, and checklist endpoints now explicitly serialize aliases; fee master create assigns `organization_id` server-side.

### LOS Sanction Contracts

- Sanction create/update/detail backend schemas now inherit from `CamelSchema`; create sets `organization_id` server-side and derives `entity_id` from the application instead of requiring the frontend to send tenant-owned fields.
- Sanction condition schemas now match actual ORM fields (`description`, `dueDate`, `complianceDate`, `waiverReason`, `uploadedDocuments`) instead of non-existent `conditionText`/`compliedOn` fields.
- Sanction security schemas now match actual ORM fields (`description`, `acceptableValue`, `netValue`, `cersaiId`, property/valuation/legal/document fields) instead of legacy collateral aliases.
- Sanction condition/security numbering and net security value are derived server-side when omitted, preserving manual entry while avoiding UI-side sequencing calculations.
- Sanction create/get/update/submit/approve/accept, condition, and security routes now explicitly serialize aliases.
- Sanction detail hook, list page, view page, and printable letter now consume camelCase DTOs only.
- Sanction service methods now call actual backend route shapes for condition updates/compliance and approval/acceptance query parameters.
- Sanction form zod schema now lives under `src/schemas/lending/`, removes `as any` submit/resolver casts, and calls react-query mutation hooks instead of logging a local draft.
- Sanction create form now posts manual terms, conditions, ongoing covenants, and securities to the normalized sanction API; covenants are represented as ongoing sanction conditions in the current domain model.

### LMS Loan Account Contracts

- Loan account create/update/response schemas now inherit from `CamelSchema`; route responses for create, update, activate, detail, summary, and DPD buckets now serialize camelCase aliases.
- Loan account creation is now derived from the accepted sanction server-side: organization, entity, product, sanctioned amount, interest terms, repayment terms, maturity, and undisbursed amount are no longer supplied by the frontend.
- Frontend loan account creation now posts `{ sanctionId }` instead of snake_case or duplicated sanction terms.
- Loan account list filters now use camelCase DTO keys (`entityId`, `productId`, `assetClassification`, `dpdFrom`, `dpdTo`, `pageSize`) and translate only to backend query-string names in the API service.
- Loan account status values are aligned to the backend enum (`CREATED`, `ACTIVE`, `DORMANT`, `FROZEN`, `CLOSED`, `WRITTEN_OFF`, `RECALLED`); NPA remains an asset classification, not an account status.
- Receipt allocation default now puts penal interest before charges, interest, and principal at the LMS account configuration level.

### LMS Disbursement Contracts

- Disbursement create/action request and response schemas now inherit from `CamelSchema`; create, approve, reject, and process endpoints serialize camelCase aliases.
- Disbursement create payload now uses `beneficiaryAccountNumber` and other camelCase field names while backend internals remain snake_case.
- Disbursement action responses now use a typed acknowledgement envelope with `disbursementId`, `approvedAmount`, `netDisbursement`, and nested `loanAccount`.
- Frontend disbursement API request/response DTOs now use camelCase fields and no longer expose snake_case mutation payloads.
- Removed unused speculative frontend disbursement service functions that pointed to non-existent routes; exported service surface now contains only actual backend endpoints.
- Disbursement list filters now use `pageSize` in the UI and translate to backend query parameters only in the API service.

### LMS Receipt And Allocation Contracts

- Receipt create, allocate, reverse, bulk import, loan-receipt list, summary, detail, and bounce endpoint schemas now inherit from `CamelSchema` and serialize camelCase aliases.
- Frontend receipt hooks and service DTOs now use camelCase mutation payloads (`loanAccountId`, `receiptAmount`, `receiptId`, `allocationMethod`, `autoAllocate`) while query-string translation remains isolated at the API boundary.
- Nested loan-account receipt schemas now derive `organizationId` server-side from the loan account instead of requiring the frontend to send tenant ownership data.
- Receipt allocation responses now use typed camelCase acknowledgement envelopes with allocation rows carrying `receiptId`, `installmentId`, `component`, `amount`, and `sequence`.
- Receipt creation UI now posts backend-aligned receipt type values and consumes camelCase create responses (`receiptNumber`, `unallocatedAmount`).
- Removed unused speculative frontend receipt service methods that pointed to non-existent cheque/template/proposed-allocation routes; exported receipt service surface now contains only actual backend endpoints.

### LMS Schedule And Accrual Contracts

- Schedule preview, generation, EMI calculation, fetch, overdue, reschedule, and mark-paid schemas now inherit from `CamelSchema` and serialize camelCase aliases.
- Frontend schedule preview DTOs now use camelCase (`interestRate`, `tenureMonths`, `disbursementDate`, `emiDay`, `calculationMethod`, `moratoriumMonths`).
- Schedule preview UI now consumes camelCase response fields (`totalInstallments`, `principalAmount`, `closingBalance`, `isMoratorium`) without per-screen snake_case access.
- Nested loan-account schedule, due-installment, and accrual schemas now serialize camelCase response aliases.

### LMS Mandate, Provision, And Adjustment Contracts

- Mandate, mandate register/cancel, asset-classification history, provision, and loan-adjustment schemas now inherit from `CamelSchema`.
- Nested loan-account mandate, classification-history, provision, and adjustment endpoints now explicitly serialize camelCase aliases.
- Tenant ownership for provision/adjustment remains server-derived through the loan-account context; frontend payloads should not carry tenant IDs.

### Collections, NPA, OTS, Restructure, And Legal Contracts

- Collection follow-up, demand notice, NPA record, penal interest, penal waiver, OTS, restructure, legal case, hearing, auction, and write-off schemas now inherit from `CamelSchema`.
- Collection action/detail endpoints now explicitly serialize camelCase aliases, not only the list endpoints.
- Frontend collection hooks now use camelCase filters (`pageSize`, `caseType`) and isolate `page_size` / `case_type` only in query-string construction.
- Removed unused speculative collection service routes that did not match the backend API shape; exported collection service methods now map to active list endpoints.
- Restructure detail screen now consumes camelCase response fields (`restructureReference`, `loanAccountId`, `preOutstandingPrincipal`, `isStandardRestructure`).

### Remaining LOS, Hidden AA/NACH, And Treasury Contracts

- Product interest-rate master schemas now inherit from `CamelSchema`; interest-rate create assigns `organizationId` server-side and all interest-rate endpoints serialize camelCase aliases.
- Credit bureau request/response schemas now inherit from `CamelSchema`; credit create/detail/analysis/summary/statistics endpoints serialize camelCase aliases and frontend credit pages now send/consume camelCase DTOs.
- Account Aggregator schemas and endpoints now serialize camelCase aliases consistently; hidden AA pages now use camelCase DTO fields while keeping query-string names only at URL construction boundaries.
- NACH batch, retry, statistics, bounce, transaction, and response-file processing schemas/endpoints now serialize camelCase aliases; hidden NACH pages and service types now send/consume camelCase DTOs.
- Standalone NPA API request/response models now use `CamelSchema`; DPD, classify, provision, batch, upgrade, write-off, summary, and movement responses serialize camelCase aliases.
- Collateral create, coverage, and valuation contracts now use camelCase request/response DTOs from the frontend; backend collateral request/response models now inherit from `CamelSchema`.
- Treasury covenant, ALM position, IRS, exposure limit, exposure tracking, and summary schemas/endpoints now serialize camelCase aliases; frontend treasury report helper DTOs no longer expose snake_case result fields.
- Backend lending route scan now shows zero `response_model` routes missing `response_model_by_alias=True`.

## Lending Module Remaining Contract Debt

Automated scan result after the current pass:

- Lending frontend/hooks/services files scanned: 182.
- Potential files containing snake_case tokens: 67. Most remaining hits are query-string parameter names, HTML IDs, legacy form field names, constants, or read-only placeholders; they still require manual reclassification before final UAT certification.
- `console.error` findings remaining in lending frontend: 0.
- `as any` findings remaining in lending frontend: 6.
- Backend lending endpoint alias findings: 0 route response models missing alias serialization.

The remaining findings are not all equal. Some are legitimate backend query parameters built inside hooks/services, but many are real DTO/form contract issues.

### High Priority Remaining Areas

| Area | Current Risk | Required Fix |
|---|---|---|
| LOS products | Core product, fee, checklist, and interest-rate contracts are normalized. | Add targeted UAT/API tests for manual interest-rate master maintenance and product lifecycle screens. |
| LOS applications | Core create/update/list wizard path and main subresources are normalized; remaining risk is older application API helpers that point to deprecated calculate/pay routes. | Remove or replace unused deprecated helpers and add tests for active manual fee/document/milestone flows. |
| LOS sanctions | Core sanction detail/list/form/condition/security contracts are normalized; remaining risk is no targeted component/API test for manual approval, acceptance, condition compliance, and edit-mode nested updates. | Add targeted tests for manual approval/acceptance/condition compliance and decide whether edit mode should manage nested conditions/securities or route those to dedicated subresource screens. |
| LMS loan accounts | Core loan account, disbursement, receipt, allocation, schedule, accrual, mandate, provision, and adjustment contracts are normalized. Remaining risk is behavioral UAT coverage, not known DTO drift. | Add targeted UAT/API tests for manual mandate recording, provision calculation, and adjustment creation. |
| Collections/NPA/OTS/restructure/legal | List, action, and detail schemas are normalized to camelCase. Remaining risk is coverage of create/edit screens that are still partly placeholder/manual. | Add targeted UAT/API tests for follow-up execution, NPA upgrade, OTS approval/payment, restructure approval/implementation, and legal hearing/auction/write-off flows. |
| AA/NACH | Hidden in manual release and contracts are now camelCase-aligned. Remaining risk is that live AA/NACH integration actions must remain unreleased. | Keep routes/screens feature-hidden; do not run portal/bank integrations in current manual UAT. |
| Treasury ALM/IRS/exposure | Borrowing, lender, covenant, ALM, IRS, exposure, and report helper contracts are normalized. | Add UAT tests for manual borrowing drawdown, lender repayment recording, ALM snapshot, and treasury dashboard metrics. |

## Other Modules Read-Only Report

This is an automated frontend-page scan for likely contract drift markers: snake_case DTO fields, direct snake_case property access, `getPaginatedItems`, `console.error`, and `as any`. Counts are indicators, not final defect counts, because some matches are legitimate constants or query-string names.

| Module | Page Files | Files With Potential Findings |
|---|---:|---:|
| accounting | 11 | 3 |
| admin | 2 | 2 |
| ap-ar | 32 | 23 |
| auth | 3 | 2 |
| bi | 18 | 13 |
| compliance | 3 | 2 |
| dms | 8 | 7 |
| ess | 17 | 8 |
| finance | 25 | 18 |
| fixed-assets | 18 | 13 |
| fixed-deposits | 8 | 7 |
| gst | 8 | 6 |
| hris | 38 | 28 |
| inventory | 14 | 0 |
| kyc | 12 | 5 |
| legal | 7 | 6 |
| masters | 18 | 12 |
| notification | 8 | 7 |
| payroll | 12 | 11 |
| portal | 20 | 15 |
| procurement | 11 | 0 |
| regulatory | 1 | 1 |
| reports | 12 | 6 |
| roles | 3 | 2 |
| settings | 1 | 1 |
| tds | 6 | 4 |
| treasury | 9 | 4 |
| users | 3 | 2 |
| vendor | 19 | 13 |
| workflow | 5 | 4 |

## Recommended Execution Order

1. Finish lending contracts before broad UAT: LOS entities, applications, products, sanctions.
2. Normalize LMS contracts: loan accounts, disbursements, schedules, receipts.
3. Normalize collections: NPA, OTS, restructure, legal.
4. Re-run typecheck and targeted loan UAT after each subdomain.
5. Keep non-lending modules unchanged until lending UAT is stable.

## Validation Completed

- `pnpm exec tsc --noEmit --pretty false` passed.
- `python3 -m py_compile` passed for touched lending API and schema modules.
- Backend lending route scan found zero typed response routes missing alias serialization.
