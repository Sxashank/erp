#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_ENV_FILE="$ROOT_DIR/deploy/production.env"
ENV_FILE="${1:-$DEFAULT_ENV_FILE}"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
RUNTIME_DIR="$ROOT_DIR/deploy/runtime"
NGINX_CONF_DIR="$RUNTIME_DIR/nginx/conf.d"
CERTBOT_WEBROOT="$RUNTIME_DIR/certbot/www"
CERTBOT_CONF="$RUNTIME_DIR/certbot/conf"
DOCKER_CMD=(docker)

log() {
  printf '\n==> %s\n' "$*"
}

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

sudo_if_needed() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo "$@"
  fi
}

os_id() {
  if [ -r /etc/os-release ]; then
    . /etc/os-release
    printf '%s' "${ID:-}"
  fi
}

install_packages() {
  if command -v dnf >/dev/null 2>&1; then
    sudo_if_needed dnf install -y "$@"
  elif command -v yum >/dev/null 2>&1; then
    sudo_if_needed yum install -y "$@"
  elif command -v apt-get >/dev/null 2>&1; then
    sudo_if_needed apt-get update
    sudo_if_needed apt-get install -y "$@"
  else
    fail "No supported package manager found. Install packages manually: $*"
  fi
}

random_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
  fi
}

set_env_value() {
  local key="$1"
  local value="$2"
  python3 - "$ENV_FILE" "$key" "$value" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
lines = path.read_text().splitlines()
needle = f"{key}="
updated = False
for idx, line in enumerate(lines):
    if line.startswith(needle):
        lines[idx] = f"{key}={value}"
        updated = True
        break
if not updated:
    lines.append(f"{key}={value}")
path.write_text("\n".join(lines) + "\n")
PY
}

ensure_env_file() {
  if [ ! -f "$ENV_FILE" ]; then
    log "Creating production env file at $ENV_FILE"
    mkdir -p "$(dirname "$ENV_FILE")"
    cp "$ROOT_DIR/deploy/production.env.example" "$ENV_FILE"
    set_env_value "POSTGRES_PASSWORD" "$(random_secret)"
    set_env_value "JWT_SECRET_KEY" "$(random_secret)"
    set_env_value "SEED_ADMIN_PASSWORD" "$(random_secret)"
    cat <<EOF

Created $ENV_FILE with generated database and JWT secrets.
Edit DOMAIN_NAME, LETSENCRYPT_EMAIL, and any SMTP/security settings, then rerun:
  $0 "$ENV_FILE"
EOF
    exit 1
  fi
}

load_env() {
  # shellcheck disable=SC1090
  set -a
  . "$ENV_FILE"
  set +a
}

validate_env() {
  [ -n "${DOMAIN_NAME:-}" ] || fail "DOMAIN_NAME is required in $ENV_FILE"
  [ "$DOMAIN_NAME" != "erp.example.com" ] || fail "Update DOMAIN_NAME in $ENV_FILE before deploying"
  [ -n "${POSTGRES_PASSWORD:-}" ] || fail "POSTGRES_PASSWORD is required"
  [ "$POSTGRES_PASSWORD" != "change-me-generate-on-server" ] || fail "POSTGRES_PASSWORD still has the example value"
  [ -n "${JWT_SECRET_KEY:-}" ] || fail "JWT_SECRET_KEY is required"
  [ "$JWT_SECRET_KEY" != "change-me-generate-on-server" ] || fail "JWT_SECRET_KEY still has the example value"
  [ -n "${CORS_ORIGINS:-}" ] || fail "CORS_ORIGINS is required"

  if [ "${RUN_SEED_DATA:-false}" = "true" ]; then
    [ -n "${SEED_ADMIN_USERNAME:-}" ] || fail "SEED_ADMIN_USERNAME is required when RUN_SEED_DATA=true"
    [ -n "${SEED_ADMIN_EMAIL:-}" ] || fail "SEED_ADMIN_EMAIL is required when RUN_SEED_DATA=true"
    [ -n "${SEED_ADMIN_PASSWORD:-}" ] || fail "SEED_ADMIN_PASSWORD is required when RUN_SEED_DATA=true"
    [ "$SEED_ADMIN_PASSWORD" != "change-me-generate-on-server" ] || fail "SEED_ADMIN_PASSWORD still has the example value"
  fi

  if [ "${ENABLE_SSL:-true}" = "true" ]; then
    [ -n "${LETSENCRYPT_EMAIL:-}" ] || fail "LETSENCRYPT_EMAIL is required when ENABLE_SSL=true"
    [ "$LETSENCRYPT_EMAIL" != "admin@example.com" ] || fail "Update LETSENCRYPT_EMAIL in $ENV_FILE before enabling SSL"
  fi
}

install_compose_plugin_binary() {
  if docker compose version >/dev/null 2>&1 || sudo docker compose version >/dev/null 2>&1; then
    return
  fi

  local arch
  case "$(uname -m)" in
    x86_64 | amd64) arch="x86_64" ;;
    aarch64 | arm64) arch="aarch64" ;;
    *) fail "Unsupported CPU architecture for Docker Compose plugin: $(uname -m)" ;;
  esac

  local version="${DOCKER_COMPOSE_VERSION:-v2.29.7}"
  local plugin_dir="/usr/local/lib/docker/cli-plugins"
  local plugin_path="$plugin_dir/docker-compose"

  log "Installing Docker Compose plugin $version"
  sudo_if_needed mkdir -p "$plugin_dir"
  sudo_if_needed curl -fsSL \
    "https://github.com/docker/compose/releases/download/$version/docker-compose-linux-$arch" \
    -o "$plugin_path"
  sudo_if_needed chmod +x "$plugin_path"
}

install_docker_on_amazon_linux() {
  log "Installing Docker on Amazon Linux"

  install_packages ca-certificates curl

  if command -v dnf >/dev/null 2>&1; then
    sudo_if_needed dnf install -y docker docker-cli || sudo_if_needed dnf install -y docker
    sudo_if_needed dnf install -y docker-compose-plugin || true
  elif command -v amazon-linux-extras >/dev/null 2>&1; then
    sudo_if_needed amazon-linux-extras install -y docker
  else
    sudo_if_needed yum install -y docker
    sudo_if_needed yum install -y docker-compose-plugin || true
  fi

  sudo_if_needed systemctl enable --now docker
  sudo_if_needed usermod -aG docker "${SUDO_USER:-$USER}" || true
  install_compose_plugin_binary
}

install_docker_if_missing() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    log "Docker and Docker Compose plugin are installed"
    return
  fi

  log "Installing Docker Engine and Compose plugin"
  if [ "$(uname -s)" != "Linux" ]; then
    fail "Automatic Docker installation is supported only on Linux. Install Docker manually and rerun."
  fi

  if ! command -v curl >/dev/null 2>&1; then
    install_packages ca-certificates curl
  fi

  if [ "$(os_id)" = "amzn" ]; then
    install_docker_on_amazon_linux
  else
    curl -fsSL https://get.docker.com | sudo_if_needed sh
    sudo_if_needed usermod -aG docker "${SUDO_USER:-$USER}" || true
    install_compose_plugin_binary
  fi

  if ! docker compose version >/dev/null 2>&1 && ! sudo docker compose version >/dev/null 2>&1; then
    fail "Docker installed, but Compose plugin is unavailable. Log out/in or install docker-compose-plugin, then rerun."
  fi
}

configure_docker_command() {
  if docker ps >/dev/null 2>&1; then
    DOCKER_CMD=(docker)
    return
  fi

  if sudo docker ps >/dev/null 2>&1; then
    DOCKER_CMD=(sudo docker)
    return
  fi

  fail "Docker is installed, but the current user cannot access it"
}

render_nginx_config() {
  local template="$1"
  mkdir -p "$NGINX_CONF_DIR" "$CERTBOT_WEBROOT" "$CERTBOT_CONF"
  sed \
    -e "s|__DOMAIN_NAME__|${DOMAIN_NAME}|g" \
    -e "s|__CLIENT_MAX_BODY_SIZE__|${NGINX_CLIENT_MAX_BODY_SIZE:-50m}|g" \
    "$template" > "$NGINX_CONF_DIR/default.conf"
}

compose() {
  local args=(--env-file "$ENV_FILE" -f "$COMPOSE_FILE")
  if [ "${ENABLE_CLAMAV:-false}" = "true" ]; then
    args+=(--profile clamav)
  fi
  "${DOCKER_CMD[@]}" compose "${args[@]}" "$@"
}

start_http_stack() {
  log "Rendering HTTP Nginx config"
  render_nginx_config "$ROOT_DIR/deploy/nginx/http.conf.template"

  log "Building and starting SMFC ERP"
  compose up -d --build db redis backend worker frontend nginx
}

issue_or_refresh_certificate() {
  if [ "${ENABLE_SSL:-true}" != "true" ]; then
    log "SSL disabled; leaving HTTP-only stack running"
    return
  fi

  local cert="$CERTBOT_CONF/live/$DOMAIN_NAME/fullchain.pem"
  if [ ! -f "$cert" ]; then
    log "Requesting Let's Encrypt certificate for $DOMAIN_NAME"
    compose --profile ssl run --rm certbot certonly \
      --webroot \
      --webroot-path /var/www/certbot \
      -d "$DOMAIN_NAME" \
      --email "$LETSENCRYPT_EMAIL" \
      --agree-tos \
      --no-eff-email \
      --non-interactive
  else
    log "Existing certificate found for $DOMAIN_NAME"
  fi

  log "Rendering HTTPS Nginx config"
  render_nginx_config "$ROOT_DIR/deploy/nginx/https.conf.template"
  compose up -d nginx
  compose exec -T nginx nginx -s reload || compose restart nginx
}

install_ssl_renewal_cron() {
  if [ "${ENABLE_SSL:-true}" != "true" ] || [ "${INSTALL_SSL_RENEWAL_CRON:-true}" != "true" ]; then
    return
  fi

  local cron_file="/etc/cron.d/smfc-erp-ssl-renew"
  local renew_script="$ROOT_DIR/deploy/renew-ssl.sh"
  log "Installing SSL renewal cron at $cron_file"
  sudo_if_needed tee "$cron_file" >/dev/null <<EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
17 3 * * * root cd "$ROOT_DIR" && "$renew_script" "$ENV_FILE" >> "$ROOT_DIR/deploy/runtime/certbot/renew.log" 2>&1
EOF
  sudo_if_needed chmod 0644 "$cron_file"
}

main() {
  ensure_env_file
  load_env
  validate_env
  install_docker_if_missing
  configure_docker_command

  mkdir -p "$RUNTIME_DIR"
  start_http_stack
  issue_or_refresh_certificate
  install_ssl_renewal_cron

  log "Deployment complete"
  if [ "${ENABLE_SSL:-true}" = "true" ]; then
    printf 'Open: https://%s\n' "$DOMAIN_NAME"
  else
    printf 'Open: http://%s\n' "$DOMAIN_NAME"
  fi
  printf 'Health: %s://%s/health\n' "$([ "${ENABLE_SSL:-true}" = "true" ] && printf https || printf http)" "$DOMAIN_NAME"
}

main "$@"
