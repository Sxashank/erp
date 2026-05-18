# SMFC ERP Production Deployment

This deployment path runs the full platform behind Nginx:

- `nginx`: public edge for HTTP/HTTPS, SPA routing, `/api/*` proxying, and ACME challenges
- `frontend`: Vite build served as static files by Nginx on the internal Docker network
- `backend`: FastAPI application with Alembic migration on startup
- `worker`: background worker using the same Python image
- `db`: PostgreSQL 15
- `redis`: Redis 7
- `certbot`: one-shot Let's Encrypt certificate issuance and renewal

No bank, GSTN, RBI, payment, email, or portal integration is enabled by this Docker setup. The platform remains manual-first; integration credentials stay tenant-level and release-gated.

## First Deployment

1. Point the domain DNS A record to the server public IP.
2. Copy and edit the production env file:

   ```bash
   cp deploy/production.env.example deploy/production.env
   nano deploy/production.env
   ```

3. Set at minimum:

   ```bash
   DOMAIN_NAME=erp.yourdomain.in
   LETSENCRYPT_EMAIL=admin@yourdomain.in
   POSTGRES_PASSWORD=<strong generated secret>
   JWT_SECRET_KEY=<strong generated secret>
   CORS_ORIGINS=https://erp.yourdomain.in
   ```

4. Run the bootstrap:

   ```bash
   ./deploy/bootstrap-prod.sh
   ```

If `deploy/production.env` does not exist, the script creates it with generated database and JWT secrets, then asks you to edit the domain and email before rerunning.

## Operations

Start or update the stack:

```bash
./deploy/bootstrap-prod.sh
```

View status:

```bash
docker compose --env-file deploy/production.env ps
```

View logs:

```bash
docker compose --env-file deploy/production.env logs -f nginx backend worker
```

Run migrations manually:

```bash
docker compose --env-file deploy/production.env exec backend alembic upgrade head
```

Renew SSL manually:

```bash
./deploy/renew-ssl.sh
```

The bootstrap installs `/etc/cron.d/smfc-erp-ssl-renew` by default when SSL is enabled.

## Seed Data

`RUN_SEED_DATA=true` runs the idempotent master seed after migrations. It creates the initial organization/admin user plus baseline masters across finance, GST, TDS, AP/AR, lending, HRIS, payroll, fixed assets, fixed deposits, inventory, compliance, DMS, ESS, legal, notifications, and BI.

Set these before the first run:

```bash
SEED_ADMIN_USERNAME=admin
SEED_ADMIN_EMAIL=admin@yourdomain.in
SEED_ADMIN_PASSWORD=<strong generated password>
```

After first successful deployment, keep `RUN_SEED_DATA=true` if you want new baseline masters added by future releases to be applied automatically; the seed checks existing codes before inserting.

## Backups

Back up PostgreSQL before every release:

```bash
docker compose --env-file deploy/production.env exec -T db pg_dump -U smfc smfc_erp > smfc_erp_$(date +%F).sql
```

Also back up Docker volumes for uploads and certs:

- `smfc-erp_uploads_data`
- `deploy/runtime/certbot/conf`

## Important Notes

- Do not rotate `JWT_SECRET_KEY` casually. The app derives tenant-secret encryption from it.
- `VITE_API_URL=/api/v1` keeps the browser on the same domain and lets Nginx proxy API traffic.
- Use `ENABLE_SSL=false` only for private network testing. Production should use `ENABLE_SSL=true`.
- Use `ENABLE_CLAMAV=true` only after the server has enough CPU/RAM for the antivirus sidecar.
