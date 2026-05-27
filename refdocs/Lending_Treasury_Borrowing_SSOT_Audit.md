# Lending, Treasury & Borrowing SSOT Audit

Date: 2026-05-26

## Scope

This audit covers lending, treasury and borrowing setup data for the SFC NBFC ERP. The platform is development-only, so demo/master seed data may be reseeded. External bank, GSTN, RBI, bureau, NACH and portal integrations are not enabled in this phase.

## Canonical Setup Surface

| Area | Canonical UI | Canonical API | Source Table | Seed Source | Consumers |
|---|---|---|---|---|---|
| Lending master catalog | `/admin/lending/masters` | `GET /api/v1/lending/masters/catalog` | catalog metadata generated from registered master models | `backend/app/db/seeds/lending_masters.py` | Settings, Lending menu, master editor |
| Generic master rows | `/admin/lending/masters/{masterKey}` | `/api/v1/lending/masters/{masterKey}/rows` | master table per catalog key | `backend/app/db/seeds/lending_masters.py` | lending setup, treasury dropdowns, reports |
| Checklist Item Catalog | `/admin/lending/masters/checklist-catalog` | `/lending/masters/checklist-catalog/rows` | `mst_checklist_item_catalog` | `backend/app/db/seeds/lending_masters.py` | product document requirements, approval checklist templates |
| Approval Checklist Templates | `/admin/lending/masters/approval-checklist-templates` | `/lending/masters/approval-checklist-templates/rows` | `mst_approval_checklist_template`, `mst_approval_checklist_item` | `backend/scripts/seed_data.py` | application checklist gating, sanction approval |
| Product Document Requirements | `/admin/lending/products/{id}/checklist` | `/lending/products/{id}/checklist` | `los_document_checklist` | `backend/scripts/seed_data.py`, `backend/scripts/seed_uat_manual_lending.py` | borrower portal upload requirements |
| Treasury option sets | `/admin/lending/masters/lending-options` | `/lending/masters/lending-options/rows?optionGroup=...` | `mst_lending_option` | `backend/app/db/seeds/lending_masters.py` | lender and borrowing forms |
| Day Count Conventions | `/admin/lending/masters/day-count-conventions` | `/lending/masters/day-count-conventions/rows` | `mst_day_count_convention` | `backend/app/db/seeds/lending_masters.py` | product and borrowing interest calculations |
| Rate Reset Benchmarks | `/admin/lending/masters/rate-reset-benchmarks` | `/lending/masters/rate-reset-benchmarks/rows` | `mst_rate_reset_benchmark` | `backend/app/db/seeds/lending_masters.py` | floating-rate borrowing/product setup |
| Funding Sources / Lenders | `/admin/treasury/lenders` | `/lending/treasury/lenders` | `los_lender` | `backend/scripts/seed_uat_manual_lending.py` | borrowing facilities, ALM, source-of-funds |
| Borrowing Facilities | `/admin/treasury/borrowings` | `/lending/treasury/borrowings` | `los_borrowing` and child tables | `backend/scripts/seed_uat_manual_lending.py` | drawdowns, repayments, ALM, spread/NII |
| Source of Funds | `/admin/treasury/source-of-funds` | `/lending/treasury/fund-deployments` | `los_fund_deployment` | `backend/scripts/seed_uat_manual_lending.py` | loan profitability and funding deployment |

## Full Master Inventory

All rows below are exposed through the same catalog API: `GET /api/v1/lending/masters/catalog` and `GET/POST/PUT/DELETE /api/v1/lending/masters/{masterKey}/rows`.

| Master key | Source table | Canonical UI | Business purpose | Primary consumers | Seed source |
|---|---|---|---|---|---|
| `asset-classes` | `mst_asset_class` | `/admin/lending/masters/asset-classes` | Asset/security classes such as vessel, port concession, shipyard leasehold and equipment | product setup, collateral setup, application appraisal | `backend/app/db/seeds/lending_masters.py` |
| `checklist-catalog` | `mst_checklist_item_catalog` | `/admin/lending/masters/checklist-catalog` | Reusable document/control item definitions | product document requirements, approval checklist templates, borrower uploads | `backend/app/db/seeds/lending_masters.py` |
| `approval-checklist-templates` | `mst_approval_checklist_template`, `mst_approval_checklist_item` | `/admin/lending/masters/approval-checklist-templates` | Sanction/appraisal gating checklist templates | application checklist cloning, sanction readiness | `backend/scripts/seed_data.py` |
| `approval-matrix` | `mst_approval_matrix` | `/admin/lending/masters/approval-matrix` | Amount-band and authority-role approval routing | sanction and disbursement approval | `backend/app/db/seeds/lending_masters.py` |
| `charge-trigger-rules` | `mst_charge_trigger_rule` | `/admin/lending/masters/charge-trigger-rules` | Event-to-charge rule setup | receipts, closure, servicing events | `backend/app/db/seeds/lending_masters.py` |
| `classification-override-policies` | `mst_classification_override_policy` | `/admin/lending/masters/classification-override-policies` | Board-approved classification exception policies | NPA/risk cockpit | `backend/app/db/seeds/lending_masters.py` |
| `communication-templates` | `mst_communication_template` | `/admin/lending/masters/communication-templates` | Borrower communication templates | notifications, portal status, servicing events | `backend/app/db/seeds/lending_masters.py` |
| `day-count-conventions` | `mst_day_count_convention` | `/admin/lending/masters/day-count-conventions` | Interest calculation day-count bases | products, borrowing facilities, ALM | `backend/app/db/seeds/lending_masters.py` |
| `document-templates` | `mst_document_template` | `/admin/lending/masters/document-templates` | KFS, sanction, certificate and notice templates | sanction letters, portal downloads, claims/certificates | `backend/app/db/seeds/lending_masters.py` |
| `fee-gl-mappings` | `mst_fee_gl_mapping` | `/admin/lending/masters/fee-gl-mappings` | Fee-to-GL accounting bridge | receipt posting, finance vouchers | `backend/app/db/seeds/lending_masters.py` |
| `fee-types` | `mst_fee_type` | `/admin/lending/masters/fee-types` | Operator-defined fee/charge categories | product fees, charges, receipts | `backend/app/db/seeds/lending_masters.py` |
| `insurance-types` | `mst_insurance_type` | `/admin/lending/masters/insurance-types` | Insurance categories required for collateral and documents | collateral setup, product controls | `backend/app/db/seeds/lending_masters.py` |
| `lending-options` | `mst_lending_option` | `/admin/lending/masters/lending-options` | Governed option groups for treasury and borrowing dropdowns | lenders, borrowing facilities, treasury setup | `backend/app/db/seeds/lending_masters.py` |
| `lifecycle-event-catalog` | `mst_lifecycle_event_catalog` | `/admin/lending/masters/lifecycle-event-catalog` | Borrower/admin lifecycle event labels and visibility defaults | application timeline, portal loan timeline | `backend/app/db/seeds/lending_masters.py` |
| `nach-return-reasons` | `mst_nach_return_reason` | `/admin/lending/masters/nach-return-reasons` | NACH bounce/return reason codes | collections, receipt exceptions | `backend/app/db/seeds/lending_masters.py` |
| `npa-buckets` | `mst_npa_bucket` | `/admin/lending/masters/npa-buckets` | DPD/SMA/NPA bucket definitions | NPA classification, risk reports | `backend/app/db/seeds/lending_masters.py` |
| `penal-charge-policies` | `mst_penal_charge_policy` | `/admin/lending/masters/penal-charge-policies` | RBI-compliant penal charge rules | collections, overdue events | `backend/app/db/seeds/lending_masters.py` |
| `provisioning-rates` | `mst_provisioning_rate` | `/admin/lending/masters/provisioning-rates` | Provisioning rates by classification/security/segment | NPA reports, provisioning MIS | `backend/app/db/seeds/lending_masters.py` |
| `rate-reset-benchmarks` | `mst_rate_reset_benchmark` | `/admin/lending/masters/rate-reset-benchmarks` | Repo/MCLR/T-bill/internal COF benchmarks | floating-rate products and borrowings | `backend/app/db/seeds/lending_masters.py` |
| `recovery-agents` | `mst_recovery_agent` | `/admin/lending/masters/recovery-agents` | Empanelled recovery agents and controls | legal collections and follow-ups | `backend/app/db/seeds/lending_masters.py` |
| `registration-authorities` | `mst_registration_authority` | `/admin/lending/masters/registration-authorities` | CERSAI, ROC, NeSL, DG Shipping and similar registries | collateral/charge registration | `backend/app/db/seeds/lending_masters.py` |
| `sla-matrix` | `mst_sla_matrix` | `/admin/lending/masters/sla-matrix` | Stage/action TAT and escalation rules | application workflow and tasks | `backend/app/db/seeds/lending_masters.py` |
| `wilful-defaulter-committees` | `mst_wilful_defaulter_committee` | `/admin/lending/masters/wilful-defaulter-committees` | Identification/review committee membership | legal recovery and NPA governance | `backend/app/db/seeds/lending_masters.py` |

## Governed Lending Option Groups

`mst_lending_option` is used only for option-set values where creating a new full master table would add complexity without improving governance. The group code is still explicit, seeded and validated server-side.

| Option group | Used by | Examples seeded | Validation point |
|---|---|---|---|
| `LENDER_TYPE` | `/admin/treasury/lenders` | Bank, DFI, NBFC, bond/NCD, commercial paper, insurance company | `TreasuryService.create_lender`, `TreasuryService.update_lender` |
| `RATING_AGENCY` | `/admin/treasury/lenders` | CRISIL, ICRA, CARE, India Ratings, Acuite | `TreasuryService.create_lender`, `TreasuryService.update_lender` |
| `PRODUCT_CATEGORY` | `/admin/lending/products`, `/admin/lending/products/new` | Term loan, project finance, working capital, cash credit, guarantee, bill discounting | `ProductService.create_product`, `ProductService.update_product` |
| `BORROWING_TYPE` | `/admin/treasury/borrowings` | Term loan, working capital, cash credit, NCD, CP, ECB, refinance | `TreasuryService.create_borrowing`, `TreasuryService.update_borrowing` |
| `RATE_TYPE` | `/admin/lending/products`, `/admin/treasury/borrowings` | Fixed, floating | `ProductService`, `TreasuryService.create_borrowing`, `TreasuryService.update_borrowing` |
| `REPAYMENT_FREQUENCY` | `/admin/lending/products`, `/admin/treasury/borrowings` | Monthly, quarterly, half-yearly, yearly, bullet | `ProductService`, `TreasuryService.create_borrowing`, `TreasuryService.update_borrowing` |
| `REPAYMENT_MODE` | `/admin/lending/products` | EMI, structured, bullet, balloon, step-up, step-down | `ProductService.create_product`, `ProductService.update_product` |
| `SECURITY_TYPE` | `/admin/treasury/borrowings` | Secured, unsecured | `TreasuryService.create_borrowing`, `TreasuryService.update_borrowing` |

## Checklist Taxonomy

| Concept | Role | Master/Transaction | Grounding Rule |
|---|---|---|---|
| Checklist Item Catalog | Reusable item definition such as PAN, audited financials, DPR, CERSAI filing | Master | Created/edited only through checklist catalog master |
| Product Document Requirements | Borrower upload requirements by product | Product setup | Must reference `catalogItemId`; code/name/category/stage are copied from catalog |
| Approval Checklist Templates | Internal appraisal/sanction gates | Master | Template items must reference `catalogItemId`; free-text items are blocked |
| Loan Checklist | Per-application live checklist | Transaction snapshot | Created by cloning approval template; carries `catalogItemId` for traceability |

## Removed / Consolidated Duplicates

| Old Surface | Status | Replacement |
|---|---|---|
| `/lending/masters/generic/*` backend router | Removed from route registration and file deleted | `/lending/masters/{masterKey}/rows` |
| Master hub rich+generic cards | Removed | Catalog-driven cards from `/lending/masters/catalog` |
| `/lending/checklist/templates/*` API | Removed from checklist router | `/lending/masters/approval-checklist-templates/rows/*` |
| `/admin/lending/checklist/templates*` UI | Redirects to canonical setup route | `/admin/lending/masters/approval-checklist-templates*` |
| Settings links for Loan Products / Approval Checklists / IIF Schemes / IIF Categories | Consolidated | one `Lending Setup` link to `/admin/lending/masters`; Loan Products remains in Lending menu |
| Product checklist route showing approval templates | Replaced | `ProductChecklistEditor` for catalog-backed borrower document requirements |
| Treasury hardcoded dropdown arrays | Removed from lender/borrowing forms | `mst_lending_option`, `mst_day_count_convention`, `mst_rate_reset_benchmark` |

## Route / Link Audit

| Route | Result |
|---|---|
| `/admin/lending/masters` | Canonical command center; lists unique catalog keys grouped by setup area |
| `/admin/lending/masters/checklist-catalog` | Reusable checklist item catalog editor |
| `/admin/lending/masters/approval-checklist-templates` | Approval checklist template list using catalog-backed items |
| `/admin/lending/checklist/templates` | Redirects to canonical approval checklist template route |
| `/admin/lending/products` | Loan product list remains the operational product setup surface |
| `/admin/lending/products/{id}/checklist` | Product document requirements editor sourced from checklist catalog |
| `/admin/treasury/lenders` | Operational funding-source/lender records; lender type and rating agency are master-backed |
| `/admin/treasury/borrowings` | Operational borrowing facilities; borrowing type, rate type, frequencies, security and benchmark are master-backed |
| `/admin/treasury/source-of-funds` | Operational borrowing-to-loan deployment workbench |
| Settings `Lending Setup` | Points to `/admin/lending/masters`; no duplicate lending setup links remain in Settings |

## Grounding Evidence

| Workflow | Evidence |
|---|---|
| Master catalog | `backend/app/api/v1/lending/masters.py` registers a single catalog and row API family with `response_model_by_alias=True` |
| Checklist template CRUD | `ChecklistTemplateService` loads `ChecklistItemCatalog` and copies code/label/category from catalog |
| Live application checklist | `LoanChecklistService._clone_template` copies `catalog_item_id` into live checklist items |
| Product document requirements | `ProductService.add_document_checklist` and `update_document_checklist` require catalog items and derive displayed fields from catalog |
| Product checklist UI | `ProductChecklistEditor` uses `useLendingMasterRows('checklist-catalog')` and sends only `catalogItemId` plus control flags |
| Product setup UI | `ProductList` and `ProductForm` use `PRODUCT_CATEGORY`, `RATE_TYPE`, `REPAYMENT_FREQUENCY`, `REPAYMENT_MODE`, and `day-count-conventions`; duplicate free-text fee/checklist tabs were removed from the product form |
| Product setup API | `LoanProduct.category`, `interest_type`, `day_count_convention`, `default_repayment_frequency`, and `default_repayment_mode` are text codes validated against their SSOT masters, not database enums |
| Product tenant guard | Product detail/update/delete, product fees and product document requirements verify the product belongs to the authenticated organization before returning or mutating rows |
| Treasury lender dropdowns | `LenderForm.tsx` uses `useLendingOptionRows('LENDER_TYPE')` and `useLendingOptionRows('RATING_AGENCY')` |
| Treasury borrowing dropdowns | `BorrowingForm.tsx` uses `BORROWING_TYPE`, `RATE_TYPE`, `REPAYMENT_FREQUENCY`, `SECURITY_TYPE`, `day-count-conventions`, and `rate-reset-benchmarks` from master APIs |
| Treasury API validation | `TreasuryService` rejects unconfigured lender/borrowing/rate/frequency/security/day-count/benchmark codes |
| Borrowing edit flow | `BorrowingUpdate` now exposes the same setup fields as the admin form and revalidates master-backed values during update |
| Seed consistency | `seed_for_organization` seeds `mst_lending_option`, checklist catalog, day-count and benchmarks; demo seeds reference those catalog rows |
| Migration validation | Local DB is at `zzc59_product_terms_master_text`; product category/rate/day-count/repayment fields are `varchar`, checklist FK backfill has zero nulls, and duplicate lending-option/checklist-catalog key counts are zero |

## Remaining Non-SSOT Boundaries

Operational records intentionally remain outside generic master editing: lenders, borrowing facilities, drawdowns, borrowing schedules, repayments, loan applications, loan accounts, receipts, fund deployments and borrower portal uploads.

## Known Adjacent Debt Outside This SSOT Change

The scan still finds older lending endpoints outside this master consolidation that use legacy `get_db` dependencies or tenant request parameters. They are not duplicate master-data systems, but they should be remediated in the next lending hardening pass: older LOS application/sanction/entity endpoints and integration-oriented services such as AA/NACH/credit/IIF request DTOs. The canonical SSOT surfaces listed above do not require `organizationId` request parameters and use camelCase wire contracts.

## Validation Checklist

| Check | Expected result |
|---|---|
| Master catalog uniqueness | One row per master key; no rich/generic duplicate cards |
| Old generic API | `/lending/masters/generic/*` not registered |
| Old template route | `/admin/lending/checklist/templates*` redirects to `/admin/lending/masters/approval-checklist-templates*` |
| Product document requirement creation | Requires `catalogItemId`; no free-text document code/name/stage/category |
| Approval template item creation | Requires `catalogItemId`; no free-text approval checklist item |
| Treasury lender setup | Lender type and rating agency loaded from `mst_lending_option` |
| Treasury borrowing setup | Borrowing type, rate type, frequency, security, day count and benchmark loaded from master APIs |
| Product term setup | Product category, rate type, repayment frequency, repayment mode and day count loaded from master APIs and validated server-side |
| Tenant API rule | SSOT APIs derive organization from authenticated tenant context, not request/query body |

## Validation Run

| Validation | Result |
|---|---|
| Alembic migration | Upgraded local DB to `zzc59_product_terms_master_text` |
| Seed validation | `python -m app.db.seeds.lending_masters` seeded missing `REPAYMENT_MODE` rows for both tenants |
| DB integrity probe | duplicate lending-option keys = 0; duplicate checklist catalog keys = 0; product checklist catalog nulls = 0; approval item catalog nulls = 0; global approval templates = 0 |
| API smoke | master catalog, option groups, products, lenders and borrowings returned HTTP 200; removed `/lending/masters/generic/*` returned HTTP 404 |
| Contract probe | product list response used camelCase keys only; invalid product category was rejected by server-side master validation |
| Static gates | focused SSOT files had no frontend snake_case DTOs, no tenant `organizationId` request params, no localStorage/mock setup data and no hardcoded dropdown option arrays |
| Type/compile | `pnpm exec tsc --noEmit` passed; lending backend `compileall` passed |
| Browser smoke | `playwright/tests/lending-ssot-smoke.spec.ts` passed on Chromium against `localhost:5176` + live backend, including canonical setup pages plus lending/treasury dashboards and reports routes |

## Product Policy Hardening Addendum

Date: 2026-05-26

This addendum covers the policy-hardening pass after the initial SSOT consolidation. The guiding rule is: workflow states remain code-owned, but business policy values that SFC may change by product or tenant must come from product setup or lending masters.

| Area | Previous risk | Final SSOT / grounding | Evidence |
|---|---|---|---|
| Product repayment frequencies | Product form only persisted the first selected repayment frequency as default | Product-owned `allowedRepaymentFrequencies` plus `defaultRepaymentFrequency` | `LoanProductBase.allowed_repayment_frequencies`, `ProductService.create_product/update_product`, `ProductForm.toPayload` |
| Product policy validation | Application create checked only amount/tenure | Product policy now validates amount, tenure, interest type, repayment frequency, repayment mode and moratorium | `ApplicationService._validate_product_policy` |
| Portal product policy | Borrower wizard could not see product document requirements before draft creation | Portal product list includes product bounds, default terms and product document requirements | `ProductListItem.document_requirements`, `PortalApplicationService.list_products`, `PortalApplicationNew` |
| Portal document upload | Borrower selected from hardcoded document types | Borrower sees product-required document rows sourced from `los_document_checklist`; mandatory rows are checked before review submit | `PortalApplicationNew.UploadStager` |
| Admin application wizard | Entity/product step used empty mock arrays | Step now loads real borrower entities and products through hooks | `Step1EntityProduct` |
| Admin loan details | Interest and repayment dropdowns were hardcoded | Product policy drives allowed interest, repayment frequency, repayment mode and moratorium bounds | `Step2LoanDetails` |
| Admin document step | Empty `mockChecklist` and simulated upload state | Product document requirements are displayed from product checklist SSOT; no fake local upload is recorded | `Step5Documents` |
| Sanction terms | Interest/repayment/security/covenant dropdowns were hardcoded | Sanction form loads rate, repayment, security nature/type and covenant options from `mst_lending_option` | `SanctionForm` |
| Sanction API/model | Interest/repayment/security fields were enum-bound | Application, sanction, loan account and loan security term fields are text policy codes with migration `zzc60_lending_policy_terms_text` | `backend/alembic/versions/zzc60_lending_policy_terms_text.py` |
| Sanction validation | Sanction terms could drift from product policy | Sanction create/update validates amount, tenure, interest type, repayment frequency/mode and moratorium against product | `SanctionService._validate_product_terms` |
| IIF scheme setup | Eligible loan types and claim frequency were hardcoded in the UI | IIF loan type and claim frequency are master-backed and server-validated | `SchemeForm`, `SubventionSchemeService._validate_option_codes` |
| Seed defaults | Missing policy option groups required manual setup | Seed adds corporate NBFC option groups for entity, sector, KYC, repayment, moratorium, security, covenant, collections, ALM and IIF | `_LENDING_OPTIONS` in `backend/app/db/seeds/lending_masters.py` |

### Current Hardcoded Boundary Review

| Boundary | Decision |
|---|---|
| Workflow statuses such as `DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, sanction approval states and portal review states | Code-owned state machine; not tenant configurable |
| Entity statuses such as `PROSPECT`, `ACTIVE`, `BLACKLISTED` | Code-owned lifecycle status for now |
| Portal session `localStorage` tokens | Auth/session persistence, not mock operational data |
| AA/NACH/credit-bureau screens | Integration-adjacent audit-only for this pass; no active external integrations are enabled |
| Legacy payment/servicing portal labels using “EMI” | Display terminology debt; core application flow now treats borrower application as SFC-only and product-policy driven |

### Validation Run For Addendum

| Validation | Result |
|---|---|
| Backend compile | `python3 -m compileall` passed for touched lending, portal, schema, model and migration files |
| Frontend typecheck | `pnpm exec tsc --noEmit --pretty false` passed |
| Static scan | Remaining active hardcoded areas are documented above; no portal application lender/source-of-funds/loan-account input fields were found in the new application wizard |

## Collections And Portal Policy Hardening Addendum

Date: 2026-05-26

This addendum covers the follow-up pass on active loan module screens after the product-policy hardening pass.

| Area | Previous risk | Final SSOT / grounding | Evidence |
|---|---|---|---|
| Entity setup policy fields | Entity type, risk grade, contact type, address type, bank account type and KYC document type were still frontend constants | Entity forms and tabs now load `ENTITY_TYPE_CORPORATE`, `RISK_GRADE`, `CONTACT_TYPE`, `ADDRESS_TYPE`, `BANK_ACCOUNT_TYPE` and KYC document types from master APIs | `EntityForm`, `EntityList`, entity tabs, `GET /lending/entities/kyc-document-types`, `EntityService._validate_entity_policy` |
| Entity policy persistence | Entity model/schema used enum-bound business classifications | Entity type, sector, risk, contact and address fields now store configured text codes and validate against lending options | `backend/app/models/lending/entity.py`, `backend/app/schemas/lending/entity.py`, migration `zzc61_entity_policy_terms_text.py` |
| OTS proposal wizard | Page used a zeroed `mockNPAAccount` and non-backend payment codes | Wizard loads real NPA accounts, captures manual outstanding components, loads `OTS_PAYMENT_MODE`, and posts a real OTS create request | `OTSWizard`, `collectionApi.createOTSProposal`, `CollectionsService.create_ots_proposal` |
| OTS payment mode | Backend schema/model was enum-bound | OTS payment mode is now a configured text code validated against `OTS_PAYMENT_MODE` | `OTSProposalCreate.payment_mode`, `OTSProposal.payment_mode`, `_validate_lending_option` |
| Restructure create | Page used `mockLoanAccounts` and hardcoded restructure/moratorium options | Page selects real loan accounts and loads `RESTRUCTURE_TYPE` and `MORATORIUM_INTEREST_TREATMENT` | `RestructureCreate`, `collectionApi.createRestructure` |
| Restructure approval | Page used a fake `mockRestructure` proposal and hardcoded authority list | Page loads actual proposal by ID, uses `APPROVAL_AUTHORITY`, and calls approve/reject APIs | `RestructureApproval`, `approveRestructure`, `rejectRestructure` |
| Restructure type | Backend schema/model was enum-bound | Restructure type is now a configured text code validated against `RESTRUCTURE_TYPE` | `LoanRestructureCreate.restructure_type`, `LoanRestructure.restructure_type`, `CollectionsService.create_restructure` |
| Portal claim document type | Portal claim upload used hardcoded document categories | Portal claim upload loads `IIF_CLAIM_DOCUMENT_TYPE` via `/portal/claims/document-types` | `PortalSubsidyReports`, `usePortalClaimDocumentTypes`, `portalClaimsApi.listDocumentTypes` |
| CamelCase API cleanup | Active LOS/LMS/collections list calls still sent snake query params | Applications, sanctions, accounts, disbursements, receipts, collections and IIF eligible-loans list APIs now accept camelCase query params from the frontend | touched API routers and frontend services/hooks |
| Tenant safety | Sanction router still used non-tenant DB dependency | Sanction router now uses `get_db_with_tenant`; active collection create/approve/get paths check loan account organization | `backend/app/api/v1/lending/sanctions.py`, `CollectionsService` |

### Validation Run For Collections Addendum

| Validation | Result |
|---|---|
| Backend compile | `python3 -m compileall` passed for touched lending and portal routers/services/schemas/models |
| Frontend typecheck | `pnpm exec tsc --noEmit --pretty false` passed |
| Static scan | Removed active `mockNPAAccount`, `mockLoanAccounts`, `mockRestructure`, and `CLAIM_DOCUMENT_TYPES` paths |
