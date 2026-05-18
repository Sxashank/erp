# Vendor Integration Runbook

This document is the master reference for going live with each of the 20 external vendors the SMFC ERP integrates with. Each vendor section lists:

- **What it's for** — the business capability.
- **Credentials needed** — what the NBFC must obtain from the vendor.
- **Where they go** — which `IntegrationConfig` fields (tenant secrets per CLAUDE.md §6.8 — NEVER `.env` / `settings.py`).
- **Feature flag** — the flip to switch on live traffic.
- **Sandbox vs production endpoints** — placeholder URLs live in `app/config.py` for platform-level knobs; tenant-specific keys stay in the DB.
- **Code locations** — client + feature flag + domain service.
- **Status** — current implementation state and what still needs finishing.

> **SaaS reminder (CLAUDE.md §6.8):** Every field listed under "tenant secret" below is different per NBFC. An NBFC's Razorpay key is theirs, not ours. It never touches `.env`. The admin UI provisions these into the `sys_integration_config` table keyed by `(organization_id, integration_type, provider)`, encrypted at rest with Fernet.

## Onboarding workflow (for every vendor)

1. NBFC signs up with vendor, gets credentials.
2. Platform admin creates an `IntegrationConfig` row via the admin UI:
   - `organization_id` = the NBFC
   - `integration_type` / `provider` = per table below
   - `config_data` = the fields listed under "tenant secret" (encrypted on write)
3. Flip the feature flag to `on` in env (or via admin UI once the flag management page ships).
4. Run the vendor's health-check endpoint (each integration client provides one).
5. Monitor `/metrics` for error rates on the new vendor for 24h.

---

## 1. GSTN Portal (Tax filing — GSTR-1 / 3B / 9 / 2B)

| Aspect                            | Value                                                                                                                                                          |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **What for**                      | File GST returns, match 2B, pull auto-draft invoices                                                                                                           |
| **Feature flag**                  | `gstn_live`                                                                                                                                                    |
| **IntegrationType**               | `GSTN`                                                                                                                                                         |
| **IntegrationProvider**           | `GSTN` (direct) / `CLEARTAX` / `ZOHO_GST` (aggregators)                                                                                                        |
| **Tenant secrets**                | `gstin`, `portal_username`, `portal_password`, `ewb_username`, `ewb_password`, `api_key` (aggregator), `api_secret` (aggregator), `client_id`, `client_secret` |
| **Platform config** (settings.py) | `GSTN_BASE_URL` (sandbox: `https://api.sandbox.gstn.gov.in`; prod: `https://api.gst.gov.in`)                                                                   |
| **Client**                        | `app/integrations/gstn/client.py`                                                                                                                              |
| **Service**                       | `app/services/gst/gstn_service.py` — 5 `TODO`s closed by this integration                                                                                      |
| **Status**                        | Scaffold complete; auth + client wired; returns mock data behind flag. **Needs:** sandbox credentials for at least one NBFC to validate end-to-end.            |

---

## 2. e-Invoice IRP (Mandatory for B2B > ₹5Cr turnover)

| Aspect                  | Value                                                                                                 |
| ----------------------- | ----------------------------------------------------------------------------------------------------- |
| **What for**            | Generate IRN + signed QR code on sales invoices                                                       |
| **Feature flag**        | `einvoice_live`                                                                                       |
| **IntegrationType**     | `E_INVOICE`                                                                                           |
| **IntegrationProvider** | `NIC_IRP` (direct) / `CLEARTAX` / `MASTERS_INDIA`                                                     |
| **Tenant secrets**      | `username`, `password`, `gstin`, `client_id`, `client_secret`                                         |
| **Platform config**     | `EINVOICE_BASE_URL` (sandbox: `https://einv-apisandbox.nic.in`; prod: `https://einvoice1.gst.gov.in`) |
| **Client**              | `app/integrations/einvoice/client.py`                                                                 |
| **Service**             | `app/services/ap_ar/sales_invoice_service.py` (GenerateEInvoice button → client)                      |
| **Status**              | Scaffold complete. **Needs:** IRP sandbox creds + NBFC's GSTIN whitelisted.                           |

---

## 3. e-Waybill (Goods movement > ₹50k)

| Aspect                  | Value                                                                         |
| ----------------------- | ----------------------------------------------------------------------------- |
| **What for**            | Generate e-waybill for goods movement                                         |
| **Feature flag**        | `ewaybill_live`                                                               |
| **IntegrationType**     | `E_WAYBILL`                                                                   |
| **IntegrationProvider** | `NIC_EWB` / `CLEARTAX`                                                        |
| **Tenant secrets**      | `username`, `password`, `gstin`, `api_key`, `api_secret`                      |
| **Platform config**     | `EWAYBILL_BASE_URL` (sandbox / prod)                                          |
| **Client**              | `app/integrations/ewaybill/client.py`                                         |
| **Status**              | Scaffold; low priority for NBFCs (mostly for movement of repossessed assets). |

---

## 4. TRACES / NSDL (TDS filing — 24Q / 26Q / Form 16A)

| Aspect              | Value                                                                                                                                                                                                                                     |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **What for**        | File quarterly TDS returns, generate Form 16A, verify challan status via OLTAS                                                                                                                                                            |
| **Feature flag**    | `tds_traces_live`                                                                                                                                                                                                                         |
| **IntegrationType** | (new — add as `TDS_TRACES`)                                                                                                                                                                                                               |
| **Tenant secrets**  | `tan`, `traces_username`, `traces_password`, `e_filing_username`, `e_filing_password`, `dsc_pfx_content` (Digital Signature Certificate, base64-encoded)                                                                                  |
| **Platform config** | `TRACES_BASE_URL`, `EFILING_BASE_URL`                                                                                                                                                                                                     |
| **Service**         | `app/services/tds/tds_return_service.py` — `file_return` method currently stub                                                                                                                                                            |
| **Status**          | **Not scaffolded** — needs new client under `app/integrations/tds/`. TRACES has no public REST API; filing goes through the government e-filing portal which requires DSC signing. Most NBFCs file via their CA — automation is optional. |

---

## 5. CKYC Registry (CERSAI — central KYC)

| Aspect                  | Value                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------ |
| **What for**            | Download a customer's KYC package by CKYC number; upload fresh KYC                               |
| **Feature flag**        | `ckyc_live`                                                                                      |
| **IntegrationType**     | `KYC`                                                                                            |
| **IntegrationProvider** | `CERSAI_CKYC`                                                                                    |
| **Tenant secrets**      | `institution_code`, `username`, `password`, `entity_code`, `dsc_pfx_content`                     |
| **Platform config**     | `CKYC_BASE_URL` (UAT: `https://test.ckycindia.in`; prod: `https://www.ckycindia.in`)             |
| **Service**             | `app/services/lending/kyc_service.py` — 2 `TODO`s closed by this integration                     |
| **Status**              | Scaffold absent. **Needs:** CERSAI institution code (NBFCs register directly with CERSAI) + DSC. |

---

## 6–8. Credit Bureaus (CIBIL, Experian, CRIF Highmark)

Three parallel integrations, all following the same shape.

| Aspect                  | CIBIL (TransUnion)                                                                                                                                                                          | Experian                          | CRIF Highmark                             |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- | ----------------------------------------- |
| **What for**            | Pull a consumer/commercial credit report                                                                                                                                                    |
| **Feature flag**        | `cibil_live`                                                                                                                                                                                | `experian_live`                   | `crif_live`                               |
| **IntegrationType**     | `CREDIT_BUREAU`                                                                                                                                                                             | `CREDIT_BUREAU`                   | `CREDIT_BUREAU`                           |
| **IntegrationProvider** | `CIBIL`                                                                                                                                                                                     | `EXPERIAN`                        | `CRIF`                                    |
| **Tenant secrets**      | `member_id`, `password`, `consumer_version`, `commercial_version`                                                                                                                           | `username`, `password`, `subcode` | `merchant_id`, `password`, `product_code` |
| **Platform config**     | `CIBIL_BASE_URL`                                                                                                                                                                            | `EXPERIAN_BASE_URL`               | `CRIF_BASE_URL`                           |
| **Webhook**             | `/webhooks/bureau/cibil` (NEW — STAGE-5-014)                                                                                                                                                | `/webhooks/bureau/experian`       | `/webhooks/bureau/crif`                   |
| **Client**              | `app/integrations/bureau/cibil.py`                                                                                                                                                          | `.../experian.py`                 | `.../crif.py` (not yet)                   |
| **Service**             | `app/services/lending/bureau_service.py`                                                                                                                                                    |
| **Status**              | CIBIL + Experian scaffolded; CRIF needs a client. Webhook routes all in place (STAGE-5-014). **Needs:** NBFC membership — each bureau signs directly with the NBFC; CIBIL is usually first. |

---

## 9. SMS (Msg91 — primary)

| Aspect                  | Value                                                                                                                                                                |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **What for**            | OTP delivery, transactional SMS for EMI reminders, collection calls                                                                                                  |
| **Feature flag**        | `sms_live`                                                                                                                                                           |
| **IntegrationType**     | `SMS`                                                                                                                                                                |
| **IntegrationProvider** | `MSG91` (primary) / `TWILIO` / `TEXTLOCAL` (fallbacks)                                                                                                               |
| **Tenant secrets**      | `auth_key`, `sender_id` (6-char DLT-registered), `dlt_template_ids` (JSON: `{"otp": "1707...", "emi_reminder": "1707..."}`), `route` (usually `4` for transactional) |
| **Platform config**     | `MSG91_BASE_URL` (default `https://api.msg91.com/api/v5`)                                                                                                            |
| **Client**              | `app/integrations/communication/sms.py` — `Msg91Provider` class                                                                                                      |
| **Status**              | Scaffold complete. **Needs:** Msg91 API key + DLT template IDs (NBFC gets DLT IDs from TRAI operator).                                                               |

---

## 10. Email (MTA — SES / Mailgun / SendGrid)

| Aspect                  | Value                                                                                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **What for**            | Statement delivery, approval notifications, auth flows                                                                                  |
| **Feature flag**        | `email_live`                                                                                                                            |
| **IntegrationType**     | `EMAIL`                                                                                                                                 |
| **IntegrationProvider** | `AWS_SES` / `SENDGRID` / `MAILGUN` / `SMTP`                                                                                             |
| **Tenant secrets**      | `api_key` (for SES/SendGrid/Mailgun), `smtp_host` / `smtp_port` / `smtp_user` / `smtp_password` (for SMTP), `from_address`, `from_name` |
| **Platform config**     | None — all vendor-specific                                                                                                              |
| **Client**              | `app/integrations/communication/email.py`                                                                                               |
| **Status**              | Scaffold complete (SES + SendGrid + SMTP). **Needs:** MTA account + verified from-domain (SPF/DKIM/DMARC aligned).                      |

---

## 11. Push Notifications (FCM + APNS)

| Aspect                  | Value                                                                                                                                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **What for**            | Mobile push for EMI due, payment confirmation, approval requests                                                                                             |
| **Feature flag**        | `push_live`                                                                                                                                                  |
| **IntegrationType**     | `PUSH`                                                                                                                                                       |
| **IntegrationProvider** | `FCM` (primary — Android + iOS via HTTP v1)                                                                                                                  |
| **Tenant secrets**      | `service_account_json` (base64-encoded Firebase service account key), `project_id`, `apns_key_id` (optional, iOS direct), `apns_team_id`, `apns_key_content` |
| **Platform config**     | `FCM_BASE_URL` (default `https://fcm.googleapis.com/v1`)                                                                                                     |
| **Client**              | `app/integrations/communication/push.py`                                                                                                                     |
| **Status**              | Scaffold complete. **Needs:** Firebase project + service account.                                                                                            |

---

## 12. Razorpay (payments + mandates)

| Aspect                  | Value                                                                           |
| ----------------------- | ------------------------------------------------------------------------------- |
| **What for**            | Accept EMI prepayments + NACH mandate setup via Razorpay Auth Link              |
| **Feature flag**        | `razorpay_live`                                                                 |
| **IntegrationType**     | `PAYMENT_GATEWAY`                                                               |
| **IntegrationProvider** | `RAZORPAY`                                                                      |
| **Tenant secrets**      | `key_id`, `key_secret`, `webhook_signing_secret` (per STAGE-5-014 webhook gate) |
| **Webhook**             | `/webhooks/payment/razorpay` (verified via STAGE-5-014 gate)                    |
| **Client**              | `app/integrations/payment_gateway/razorpay.py`                                  |
| **Status**              | End-to-end implementation complete. **Needs:** Razorpay keys per NBFC.          |

---

## 13. Paytm (payments)

| Aspect                  | Value                                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------------- |
| **What for**            | Accept EMI prepayments via Paytm Gateway                                                                |
| **Feature flag**        | `paytm_live`                                                                                            |
| **IntegrationType**     | `PAYMENT_GATEWAY`                                                                                       |
| **IntegrationProvider** | `PAYTM` (new — added in STAGE-5-014)                                                                    |
| **Tenant secrets**      | `merchant_id`, `merchant_key`, `webhook_signing_secret`                                                 |
| **Webhook**             | `/webhooks/payment/paytm` (verified) — domain handling TODO                                             |
| **Status**              | Webhook gate wired (STAGE-5-014). Client not yet built. **Needs:** Paytm Business merchant credentials. |

---

## 14. CCAvenue (payments)

| Aspect                  | Value                                                                                                       |
| ----------------------- | ----------------------------------------------------------------------------------------------------------- |
| **What for**            | Accept EMI prepayments via CCAvenue (net-banking heavy)                                                     |
| **Feature flag**        | `ccavenue_live`                                                                                             |
| **IntegrationType**     | `PAYMENT_GATEWAY`                                                                                           |
| **IntegrationProvider** | `CCAVENUE`                                                                                                  |
| **Tenant secrets**      | `merchant_id`, `access_code`, `working_key`, `webhook_signing_secret`                                       |
| **Webhook**             | `/webhooks/payment/ccavenue` (verified) — `encResp` decryption TODO                                         |
| **Status**              | Webhook gate wired. **Needs:** CCAvenue merchant credentials + working key for AES decryption of `encResp`. |

---

## 15. NACH (bank mandate + auto-debit)

| Aspect                  | Value                                                                                                                                                                              |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **What for**            | Set up NACH mandate for EMI auto-debit; process debit batches; reconcile response files                                                                                            |
| **Feature flag**        | `nach_live`                                                                                                                                                                        |
| **IntegrationType**     | `NACH`                                                                                                                                                                             |
| **IntegrationProvider** | `NPCI_DIRECT` (sponsor-bank NACH) / `RAZORPAY_NACH` / `CASHFREE_NACH`                                                                                                              |
| **Tenant secrets**      | `sponsor_bank_name`, `corporate_id`, `utility_code`, `sftp_host`, `sftp_user`, `sftp_password`, `pfx_content` (DSC for NACH files), `pfx_password`                                 |
| **Webhook**             | `/webhooks/nach/razorpay` (existing, env-based; should migrate to gate), `/webhooks/nach/cashfree` (same)                                                                          |
| **Client**              | `app/integrations/nach/client.py` + `file_generator.py`                                                                                                                            |
| **Status**              | File generation scaffold complete (NACH 2.0 format). **Needs:** sponsor-bank sign-up — each NBFC partners with a scheduled commercial bank for NACH (typically HDFC / Axis / Yes). |

---

## 16. CERSAI (central security-interest registry)

| Aspect              | Value                                                                        |
| ------------------- | ---------------------------------------------------------------------------- |
| **What for**        | Register security interest on charged assets (mandatory for secured lending) |
| **Feature flag**    | `cersai_live`                                                                |
| **IntegrationType** | `CERSAI`                                                                     |
| **Tenant secrets**  | `entity_code`, `user_id`, `password`, `dsc_pfx_content`                      |
| **Platform config** | `CERSAI_BASE_URL`                                                            |
| **Client**          | `app/integrations/cersai/client.py`                                          |
| **Status**          | Scaffold complete. **Needs:** CERSAI entity registration + DSC.              |

---

## 17. NeSL (digital loan documentation)

| Aspect              | Value                                                                |
| ------------------- | -------------------------------------------------------------------- |
| **What for**        | Generate legally-enforceable digital loan contracts (IBC-recognised) |
| **Feature flag**    | `nesl_live`                                                          |
| **IntegrationType** | (new — add as `NESL`)                                                |
| **Tenant secrets**  | `lender_code`, `username`, `password`, `dsc_pfx_content`             |
| **Platform config** | `NESL_BASE_URL`                                                      |
| **Status**          | **Not scaffolded.** Needs new client under `app/integrations/nesl/`. |

---

## 18. e-Sign (Aadhaar + document e-sign)

| Aspect                  | Value                                                                                          |
| ----------------------- | ---------------------------------------------------------------------------------------------- |
| **What for**            | Aadhaar-based e-sign on loan agreements                                                        |
| **Feature flag**        | `esign_live`                                                                                   |
| **IntegrationType**     | `E_SIGN`                                                                                       |
| **IntegrationProvider** | `NSDL_ESIGN` / `CDSL_ESIGN` / `DIGIO`                                                          |
| **Tenant secrets**      | `asp_id`, `client_id`, `client_secret`, `ekyc_service_id`                                      |
| **Platform config**     | `ESIGN_BASE_URL`                                                                               |
| **Client**              | `app/integrations/esign/` (Aadhaar flow scaffolded)                                            |
| **Status**              | Scaffold complete for NSDL flow. **Needs:** ASP registration with NSDL/CDSL (takes 2-4 weeks). |

---

## 19. Redis (managed — ElastiCache / Upstash / Aiven)

| Aspect              | Value                                                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **What for**        | Cache + Arq job queue + rate-limit buckets + session store                                                                         |
| **Feature flag**    | N/A — always on                                                                                                                    |
| **Platform config** | `REDIS_URL` (single platform-wide, not per-tenant)                                                                                 |
| **Status**          | Dev uses docker-compose Redis. **Needs:** managed Redis provisioning (ElastiCache is the default pick for AWS-hosted deployments). |

---

## 20. CRILC Export (regulatory monthly submission)

| Aspect              | Value                                                                                                               |
| ------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **What for**        | Monthly RBI submission of large-exposure data (₹5Cr+ per borrower)                                                  |
| **Feature flag**    | `crilc_live` (not yet added)                                                                                        |
| **IntegrationType** | (new — `CRILC`)                                                                                                     |
| **Tenant secrets**  | `rbi_reporting_code`, `sftp_host`, `sftp_user`, `sftp_password`, `pgp_public_key` (RBI's public key for encryption) |
| **Platform config** | `CRILC_SFTP_HOST`                                                                                                   |
| **Worker**          | `app/workers/arq_worker.py::export_crilc_monthly` — currently noop                                                  |
| **Status**          | **Not scaffolded.** RBI delivery is SFTP + PGP-encrypted fixed-width files.                                         |

---

## Provisioning checklist

For a new NBFC going live, the sequence is usually:

1. **Must-have at day-1 go-live:**
   - Razorpay or Paytm (for portal payments)
   - Msg91 (for OTP)
   - SMTP / SES (for email)
   - CIBIL (for credit checks)
   - NACH sponsor bank (for EMI auto-debit)
2. **Within 30 days:**
   - GSTN (if the NBFC does B2B invoicing)
   - CKYC (must — RBI mandate)
   - e-Sign (loan document signing)
3. **Within 90 days:**
   - Experian / CRIF (cross-bureau corroboration)
   - CERSAI (for secured lending)
   - CRILC (first monthly filing due within 60 days of licence activation)
4. **Optional:**
   - e-Invoice (only if turnover threshold met)
   - e-Waybill (only if goods movement)
   - NeSL (digital loan contracts — optional but best-practice)
   - Push (mobile app — many NBFCs skip initially)
