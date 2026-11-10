#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/gemma4-api-server
ENV_FILE=/etc/gemma4-api-server.env
SUDO=
if [ "$(id -u)" -ne 0 ]; then SUDO=sudo; fi

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
$SUDO mkdir -p "$APP_DIR"
$SUDO install -m 755 "$SCRIPT_DIR/gemma_api.py" "$APP_DIR/gemma_api.py"
$SUDO useradd --system --home /nonexistent --shell /usr/sbin/nologin gemma-api 2>/dev/null || true

if [ ! -s "$ENV_FILE" ]; then
  KEY="$(openssl rand -hex 24)"
  {
    printf 'GEMMA_API_KEY=%s\n' "$KEY"
    printf 'GEMMA_UPSTREAM_URL=%s\n' "http://127.0.0.1:18080"
    printf 'GEMMA_BIND_HOST=127.0.0.1\n'
    printf 'GEMMA_BIND_PORT=%s\n' "18081"
    printf 'GEMMA_MAX_BODY_BYTES=%s\n' "67108864"
  } | $SUDO tee "$ENV_FILE" >/dev/null
  $SUDO chmod 600 "$ENV_FILE"
fi

$SUDO install -m 644 "$SCRIPT_DIR/gemma-api.service" /etc/systemd/system/gemma-api.service
$SUDO systemctl daemon-reload
$SUDO systemctl enable --now gemma-api.service
echo "Installed. Read the key from $ENV_FILE locally; do not publish it."
