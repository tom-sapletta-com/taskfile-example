# Taskfile + Markpact Project

**Cały projekt w jednym pliku README.md — wypakuj i uruchom przez Taskfile.**

## 📋 Co to jest?

Ten projekt demonstruje podejście **Single-File Project** z wbudowanymi komendami CLI:

1. **README.md** zawiera wszystkie pliki jako bloki `markpact:file path=...`
2. **Taskfile.yml** jest krótki (~90 linii) — definiuje taski specyficzne dla projektu
3. **`taskfile` CLI** dostarcza wbudowane komendy (doctor, setup, deploy, clean, push, e2e) — **zero skryptów bash**
4. **markpact** wypakowuje pliki, **taskfile** zarządza projektem

> **Zmiana architektury:** Wcześniej logika deploymentu była w `scripts/*.sh`.
> Teraz jest wbudowana w `taskfile` CLI — nie trzeba duplikować skryptów w projektach.

## 🏗️ Architektura

**Networking:** Traefik reverse proxy z automatycznym TLS (Let's Encrypt).  
- **Lokalnie:** `docker compose` z portami 8000, 3000
- **Prod:** Podman Quadlet + Traefik (porty 80/443, automatyczny SSL)
- **Domeny:** Web (`web.example.com`), Landing (`landing.example.com`)

```
README.md (ten plik)
    │
    ├─ markpact:file path=Taskfile.yml      → Taski projektowe (krótki YAML)
    ├─ markpact:file path=scripts/init.sh   → Inicjalizacja (venv, prompts)
    ├─ markpact:file path=scripts/generate.sh → Generowanie kodu (Aider)
    ├─ markpact:file path=prompts/*.md       → Prompty dla AI
    └─ markpact:file path=docker-compose.yml → Docker
    │
    └─► markpact README.md (wypakowuje)
    │
    ▼
./sandbox/
    ├── Taskfile.yml       → Taski projektowe (build, deploy, dev, stop, logs)
    ├── scripts/           → Tylko skrypty specyficzne dla projektu
    │   ├── init.sh        → Inicjalizacja (venv, zależności, prompts)
    │   └── generate.sh    → Generowanie kodu przez Aider
    ├── .env               → Konfiguracja lokalna (porty, klucze API)
    ├── .env.staging       → Konfiguracja staging (domeny, hosty)
    ├── .env.prod          → Konfiguracja produkcji (domeny, hosty)
    ├── Dockerfile         → Obraz bazowy (python:3.12-slim)
    ├── docker-compose.yml → Konfiguracja Docker
    ├── deploy/quadlet/    → Podman Quadlet units (systemd)
    ├── prompts/           → Prompty dla Aidera
    ├── apps/              → Wygenerowane aplikacje
    └── VERSION            → Wersja projektu

Wbudowane komendy CLI (nie wymagają skryptów):
    taskfile doctor        → Diagnostyka (SSH, tools, porty, remote health)
    taskfile setup env     → Konfiguracja .env (porty, projekt)
    taskfile setup hosts   → Konfiguracja hostów (staging/prod)
    taskfile setup prod    → Setup produkcji (SSH, podman, dysk)
    taskfile deploy        → Deploy (auto-strategia: compose/ssh_push/quadlet)
    taskfile push          → Transfer obrazów Docker → serwer (bez registry)
    taskfile clean         → Czyszczenie artefaktów
    taskfile e2e           → Testy end-to-end usług i IaC
```

## 🎯 Workflow

### Instalacja i przygotowanie

```bash
# 1. Instalacja narzędzi
pip install markpact taskfile --upgrade

# 2. Wypakowanie projektu
markpact README.md
cd sandbox

# 3. Inicjalizacja projektu (venv, prompts)
taskfile run init

# 4. Konfiguracja (wbudowane komendy CLI — interaktywne)
taskfile setup env         # Konfiguruje porty, nazwę projektu
taskfile setup hosts       # Konfiguruje hosty deploymentu
taskfile setup prod        # Setup produkcji (SSH test, podman install)
```

### Generowanie kodu i rozwój lokalny

```bash
# Generowanie kodu przez Aider (web, desktop, landing)
taskfile run generate

# Start lokalny z Docker
taskfile run dev

# Diagnostyka
taskfile doctor
taskfile doctor -v         # + remote health, SSH connectivity
taskfile --env prod doctor --remote  # Diagnostyka na serwerze produkcyjnym
```

### Build i deploy

```bash
# Build obrazów Docker
taskfile run build

# Transfer obrazów na serwer (wymagane przed deploy!)
taskfile push taskfile-example-web:latest taskfile-example-landing:latest

# Deploy na prod (SSH → podman) — wymaga wcześniejszego push
taskfile --env prod run deploy

# Sprawdź czy obrazy są na serwerze
taskfile --env prod doctor --remote

# Dry-run (podgląd komend bez uruchamiania)
taskfile --env prod --dry-run run deploy
```

### Testowanie e2e

```bash
# Testy usług i IaC (wbudowany e2e runner)
taskfile e2e                          # Lokalne testy
taskfile e2e --env prod               # Testy na produkcji
taskfile e2e --env prod --check-only  # Tylko sprawdzenie (bez deploy)
```

### Monitorowanie i zarządzanie

```bash
# Status
taskfile run status                   # Lokalny (docker compose ps)
taskfile --env prod run status        # Prod (SSH → podman ps)

# Logi
taskfile run logs                     # Lokalne
taskfile --env prod run logs          # Prod (SSH → podman logs)

# Stop
taskfile run stop                     # Lokalny
taskfile --env prod run stop          # Prod

# Czyszczenie
taskfile clean                        # Interaktywne (3 poziomy)
taskfile clean --level 1 --yes        # Tylko apps/
```

## 🚨 Rozwiązywanie problemów

### DNS — timeout Let's Encrypt

Jeśli widzisz w logach Traefik:
```
lookup acme-v02.api.letsencrypt.org on 10.89.0.1:53: i/o timeout
```

**Przyczyna:** Podman network DNS (10.89.0.1) nie rozwiazuje zewnętrznych domen.

**Rozwiązanie 1 — resolv.conf mount (zalecane):**
```bash
# Utwórz deploy/resolv.conf z publicznym DNS:
echo -e 'search dns.podman\nnameserver 8.8.8.8\nnameserver 1.1.1.1' > deploy/resolv.conf

# W deploy/quadlet/traefik.container dodaj:
Volume=/home/tom/sandbox/deploy/resolv.conf:/etc/resolv.conf:ro
```

**Rozwiązanie 2 — UFW firewall (jeśli ufw blokuje FORWARD):**
```bash
# Na serwerze: zezwól na ruch z podman subnet
ufw route allow in on podman1 out on ens6 from 10.89.0.0/24 to any
ufw route allow in on ens6 out on podman1 to 10.89.0.0/24
iptables -t nat -A POSTROUTING -s 10.89.0.0/24 -j MASQUERADE
```

**Wdrożenie:**
```bash
taskfile --env prod run deploy   # wyślij pliki
taskfile --env prod run restart  # restart Traefik
taskfile --env prod run logs     # sprawdź logi
```

### SSL — certyfikaty nie działają

```bash
# Sprawdź logi
taskfile --env prod run logs | grep -i "acme\|error"

# Napraw automatycznie
taskfile --env prod run fix
```

## 🔧 Dostępne komendy

### Taski projektowe (z Taskfile.yml)

| Komenda | Opis |
|---------|------|
| `taskfile run init` | Tworzy strukturę katalogów, instaluje zależności |
| `taskfile run generate` | Generuje kod przez Aider (web, desktop, landing) |
| `taskfile run build` | Build Docker images |
| `taskfile run deploy` | Deploy (`@local` compose / `@remote` quadlet) |
| `taskfile run rollback` | Cofnij do poprzedniej wersji kontenerów |
| `taskfile run dev` | Start lokalny z hot-reload |
| `taskfile run stop` | Stop serwisów (`@local`/`@remote`) |
| `taskfile run restart` | Restart serwisów bez rebuild |
| `taskfile run logs` | Logi (`@local`/`@remote`) |
| `taskfile run status` | Status serwisów (`@local`/`@remote`) |
| `taskfile run health` | Health check z retry logic |
| `taskfile run urls` | Wyświetl wszystkie URL-e |
| `taskfile run backup` | Backup certyfikatów i konfiguracji |
| `taskfile run watch` | Ciągły monitoring (5s interval) |
| `taskfile run alert` | Sprawdź i wyślij alert jeśli DOWN |
| `taskfile run fix` | Auto-naprawa problemów |

### Wbudowane komendy CLI (nie wymagają Taskfile.yml)

| Komenda | Opis |
|---------|------|
| `taskfile doctor` | 🔧 5-warstwowa diagnostyka (preflight, validation, env, fix, LLM) |
| `taskfile doctor -v` | 🔧 + remote health, SSH connectivity |
| `taskfile --env prod doctor --remote` | 🔧 Diagnostyka na serwerze produkcyjnym (SSH, podman, dysk) |
| `taskfile setup env` | 🔐 Konfiguracja .env (porty, projekt) |
| `taskfile setup hosts` | 🌐 Konfiguracja hostów staging/prod |
| `taskfile setup prod` | 🚀 Setup produkcji (SSH, podman, dysk) |
| `taskfile push IMAGE...` | 📦 Transfer obrazów Docker → serwer via SSH |
| `taskfile deploy` | 🚀 Auto-deploy (compose / ssh_push / quadlet) |
| `taskfile clean` | 🧹 Czyszczenie artefaktów (3 poziomy) |
| `taskfile e2e` | 🧪 Testy end-to-end usług i IaC |
| `taskfile list` | Lista tasków |
| `taskfile validate` | Walidacja Taskfile.yml |

---

## Pliki projektu (markpact)

### Taskfile.yml — konfiguracja tasków

```markpact:file path=Taskfile.yml
version: "1"
name: sandbox
description: "Sandbox — local Docker Compose + remote Podman Quadlet deploy"

variables:
  APP_NAME: sandbox
  TAG: latest
  WEB_IMAGE: sandbox-web
  LANDING_IMAGE: sandbox-landing
  WEB_CONTAINER: web
  LANDING_CONTAINER: landing
  COMPOSE: docker compose
  RESTART_DELAY: "3"
  # URLs — derived from env vars loaded from .env files
  WEB_URL: "https://${WEB_DOMAIN:-localhost}"
  LANDING_URL: "https://${LANDING_DOMAIN:-localhost}"
  TRAEFIK_DASHBOARD: "http://${WEB_DOMAIN:-localhost}:8080"
  # Ports — local dev
  PORT_WEB: "8001"
  PORT_LANDING: "3001"

environment_defaults:
  ssh_user: root
  container_runtime: podman
  service_manager: quadlet

environments:
  local:
    container_runtime: docker
    compose_command: docker compose
    env_file: .env

  staging:
    ssh_host: ${STAGING_HOST}
    env_file: .env.staging

  prod:
    ssh_host: ${PROD_HOST}
    env_file: .env.prod

tasks:
  # ─── Build & Deploy ─────────────────────────────────
  # Workflow: build → export-images → deploy → health
  #   taskfile run build                    # zbuduj obrazy lokalnie
  #   taskfile run export-images            # wyeksportuj do /tmp
  #   taskfile --env prod run deploy        # wdróż na serwer
  #   taskfile --env prod run health        # sprawdź czy działa

  build:
    desc: Build Docker images locally
    env: [local]
    cmds:
      - ${COMPOSE} build

  export-images:
    desc: Export Docker images to /tmp (run before remote deploy)
    env: [local]
    deps: [build]
    cmds:
      - echo '📤 Eksport web...' && docker save ${WEB_IMAGE}:latest | gzip > /tmp/web.tar.gz
      - echo '📤 Eksport landing...' && docker save ${LANDING_IMAGE}:latest | gzip > /tmp/landing.tar.gz
      - echo '✅ Obrazy wyeksportowane → taskfile --env prod run deploy'

  validate-deploy:
    desc: Pre-deploy validation — check quadlet files and configs exist
    silent: true
    cmds:
      - test -f deploy/quadlet/web.container || (echo '❌ Brak deploy/quadlet/web.container' && exit 1)
      - test -f deploy/quadlet/landing.container || (echo '❌ Brak deploy/quadlet/landing.container' && exit 1)
      - test -f deploy/quadlet/traefik.container || (echo '❌ Brak deploy/quadlet/traefik.container' && exit 1)
      - test -f deploy/quadlet/proxy.network || (echo '❌ Brak deploy/quadlet/proxy.network' && exit 1)
      - test -f deploy/traefik.yml || (echo '❌ Brak deploy/traefik.yml' && exit 1)
      - test -f deploy/traefik-dynamic.yml || (echo '❌ Brak deploy/traefik-dynamic.yml' && exit 1)
      - echo '✅ Deploy artifacts OK'

  preflight:
    desc: Check remote server readiness (podman, UFW, disk, dirs)
    env: [staging, prod]
    cmds:
      - "@remote podman --version > /dev/null 2>&1 && echo '   ✅ podman OK' || (echo '   ❌ podman nie zainstalowany! apt install -y podman' && exit 1)"
      - "@remote grep -q 'ACCEPT' /etc/default/ufw 2>/dev/null && echo '   ✅ UFW FORWARD=ACCEPT' || echo '   ⚠️ UFW FORWARD!=ACCEPT — kontenery mogą nie mieć sieci'"
      - "@remote df -h / | tail -1 | awk '{if ($5+0 > 90) {print \"   ❌ Dysk zapełniony: \" $5; exit 1} else print \"   ✅ Dysk OK: \" $5}'"
      - "@remote mkdir -p /etc/containers/systemd /home/tom/sandbox/deploy /home/tom/sandbox/letsencrypt"
      - "@remote echo '   ✅ Katalogi OK'"

  deploy:
    desc: Deploy to target environment
    env: [local, staging, prod]
    cmds:
      # --- Local deploy (docker compose) ---
      - "@local ${COMPOSE} up -d"
      - "@local echo '✅ Local deploy done → taskfile run health'"
      # --- Remote deploy (podman quadlet) ---
      # 1. Backup bieżących obrazów na wypadek rollback
      - "@remote podman tag ${WEB_IMAGE}:latest ${WEB_IMAGE}:prev 2>/dev/null || true"
      - "@remote podman tag ${LANDING_IMAGE}:latest ${LANDING_IMAGE}:prev 2>/dev/null || true"
      # 2. Transfer obrazów na serwer (save → scp → load)
      - "@push /tmp/web.tar.gz /tmp/landing.tar.gz /tmp/"
      - "@remote echo '📥 Import web...' && gunzip -c /tmp/web.tar.gz | podman load"
      - "@remote echo '📥 Import landing...' && gunzip -c /tmp/landing.tar.gz | podman load"
      - "@remote rm -f /tmp/web.tar.gz /tmp/landing.tar.gz"
      # 3. Skopiuj pliki konfiguracyjne
      - "@push deploy/quadlet/*.container deploy/quadlet/*.network /etc/containers/systemd/"
      - "@push deploy/traefik.yml deploy/traefik-dynamic.yml deploy/resolv.conf /home/tom/sandbox/deploy/"
      # 4. Reload i graceful restart
      - "@remote systemctl daemon-reload"
      - "@remote systemctl stop web landing 2>/dev/null || true"
      - "sleep ${RESTART_DELAY}"
      - "@remote systemctl start traefik web landing"
      # 5. Weryfikacja
      - "sleep 5"
      - "@remote echo '' && echo '🚀 Deploy complete!'"
      - "@remote podman ps --format '   {{.Names}}: {{.Status}}' | grep -E 'web|landing|traefik'"
      - "@remote systemctl is-active traefik web landing && echo '   ✅ Wszystkie serwisy aktywne' || echo '   ⚠️ Nie wszystkie serwisy aktywne'"

  rollback:
    desc: Rollback to previous container version
    env: [staging, prod]
    cmds:
      - "@remote echo '🔄 Rollback — przywracanie poprzedniej wersji...' && echo ''"
      # 1. Sprawdź czy istnieją obrazy :prev
      - "@remote podman image exists ${WEB_IMAGE}:prev && echo '   ✅ ${WEB_IMAGE}:prev found' || (echo '   ❌ Brak obrazu :prev' && exit 1)"
      - "@remote podman image exists ${LANDING_IMAGE}:prev && echo '   ✅ ${LANDING_IMAGE}:prev found' || (echo '   ❌ Brak obrazu :prev' && exit 1)"
      # 2. Przywróć :prev jako :latest
      - "@remote podman tag ${WEB_IMAGE}:prev ${WEB_IMAGE}:latest"
      - "@remote podman tag ${LANDING_IMAGE}:prev ${LANDING_IMAGE}:latest"
      # 3. Graceful restart (stop → delay → start)
      - "@remote systemctl stop web landing"
      - "sleep ${RESTART_DELAY}"
      - "@remote systemctl start web landing"
      - "sleep 3"
      - "@remote echo '' && echo '✅ Rollback complete!'"
      - "@remote podman ps --format '   {{.Names}}: {{.Status}}' | grep -E 'web|landing'"

  # ─── Development ──────────────────────────────────────
  #   taskfile run dev     # uruchom lokalnie z hot-reload
  #   taskfile run logs    # podgląd logów
  #   taskfile run stop    # zatrzymaj

  dev:
    desc: Start local dev with hot-reload
    env: [local]
    cmds:
      - ${COMPOSE} up -d --build
      - echo "✅ Dev running at http://localhost:${PORT_WEB}"
      - echo "💡 Następne kroki → taskfile run logs | taskfile run stop"
      - ${COMPOSE} logs -f

  # ─── Operations ───────────────────────────────────────
  #   taskfile --env prod run stop     # zatrzymaj
  #   taskfile --env prod run status   # pokaż status
  #   taskfile --env prod run logs     # pokaż logi
  #   taskfile --env prod run health   # pełny health check

  stop:
    desc: Stop services
    env: [local, staging, prod]
    cmds:
      - "@local ${COMPOSE} down"
      - "@remote systemctl stop web landing 2>/dev/null || true"
      - "@remote echo '✅ Serwisy zatrzymane'"

  restart:
    desc: Graceful restart services (stop → delay → start)
    env: [local, staging, prod]
    cmds:
      - "@local ${COMPOSE} restart"
      - "@remote systemctl stop traefik web landing 2>/dev/null || true"
      - "sleep ${RESTART_DELAY}"
      - "@remote systemctl start traefik web landing"
      - "@remote echo '✅ Serwisy zrestartowane → taskfile --env prod run health'"

  logs:
    desc: View logs (last 30 lines)
    env: [local, staging, prod]
    cmds:
      - "@local ${COMPOSE} logs --tail 50"
      - "@remote echo '=== traefik ===' && journalctl -u traefik --no-pager -n 10 --output=cat"
      - "@remote echo '=== web ===' && podman logs --tail 15 ${WEB_CONTAINER} 2>/dev/null || true"
      - "@remote echo '=== landing ===' && podman logs --tail 15 ${LANDING_CONTAINER} 2>/dev/null || true"

  status:
    desc: Show service status and URLs
    env: [local, staging, prod]
    cmds:
      - "@local ${COMPOSE} ps"
      - "@remote echo '📦 Running containers:' && podman ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'"
      - "@remote echo '' && echo '📊 Systemd services:' && systemctl is-active traefik web landing || true"
      - "@remote echo '' && echo '🔗 URLs:' && echo '   📱 Web:     ${WEB_URL}' && echo '   🌐 Landing: ${LANDING_URL}' && echo '   📊 Traefik: ${TRAEFIK_DASHBOARD}'"

  health:
    desc: Health check with retry logic
    env: [local, staging, prod]
    retries: 3
    retry_delay: 5
    cmds:
      - "@local echo '🏠 Local health check:'"
      - "@local curl -sf http://localhost:${PORT_WEB}/health > /dev/null && echo '   ✅ Web OK' || echo '   ❌ Web not responding'"
      - "@local curl -sf http://localhost:${PORT_LANDING} > /dev/null && echo '   ✅ Landing OK' || echo '   ❌ Landing not responding'"
      - "@remote echo '🌐 Remote health check:' && echo ''"
      - "@remote podman ps --format '   {{.Names}}: {{.Status}}' | grep -E 'web|landing|traefik'"
      - "@remote systemctl is-active traefik && echo '   ✅ traefik active' || echo '   ❌ traefik inactive'"
      - "@remote systemctl is-active web && echo '   ✅ web active' || echo '   ❌ web inactive'"
      - "@remote systemctl is-active landing && echo '   ✅ landing active' || echo '   ❌ landing inactive'"
      - "@remote curl -sf http://localhost:8000/health > /dev/null && echo '   ✅ Web /health responds' || echo '   ❌ Web /health not responding'"
      - "@remote curl -sf http://localhost:3000/ > /dev/null && echo '   ✅ Landing responds' || echo '   ❌ Landing not responding'"
      - "@remote curl -sfk https://${WEB_DOMAIN}/health > /dev/null 2>&1 && echo '   ✅ HTTPS OK' || echo '   ⚠️ HTTPS not ready (cert pending or DNS issue)'"

  urls:
    desc: Show all service URLs
    env: [local, staging, prod]
    cmds:
      - "@local echo '🏠 Local:' && echo '   📱 Web:     http://localhost:${PORT_WEB}' && echo '   🌐 Landing: http://localhost:${PORT_LANDING}'"
      - "@remote echo '🌐 Remote:' && echo '   📱 Web:     ${WEB_URL}' && echo '   🌐 Landing: ${LANDING_URL}' && echo '   📊 Traefik: ${TRAEFIK_DASHBOARD}'"

  fix:
    desc: Auto-detect and fix common issues
    env: [staging, prod]
    cmds:
      - "@remote echo '🔧 Diagnostyka automatyczna...' && echo ''"
      # Fix 1: Restart jeśli kontenery nie działają
      - "@remote podman ps | grep -q web && echo '   ✅ web działa' || (echo '   ❌ web nie działa → restarting' && systemctl restart web)"
      - "@remote podman ps | grep -q landing && echo '   ✅ landing działa' || (echo '   ❌ landing nie działa → restarting' && systemctl restart landing)"
      # Fix 2: Reload traefik jeśli nie odpowiada
      - "@remote curl -sf http://localhost:8080/api/overview > /dev/null && echo '   ✅ traefik OK' || (echo '   ❌ traefik nie odpowiada → restarting' && systemctl restart traefik)"
      # Fix 3: Sprawdź DNS
      - "@remote dig +short acme-v02.api.letsencrypt.org > /dev/null 2>&1 && echo '   ✅ DNS OK' || echo '   ⚠️ DNS problem — sprawdź /etc/resolv.conf'"
      # Fix 4: Cleanup
      - "@remote podman container prune -f 2>/dev/null && echo '   🧹 Wyczyszczono martwe kontenery'"
      - "@remote podman image prune -f 2>/dev/null && echo '   🧹 Wyczyszczono wiszące obrazy'"
      - "@remote echo '' && echo '✅ Naprawa zakończona → taskfile --env prod run health'"

  backup:
    desc: Backup Lets Encrypt certs and config
    env: [staging, prod]
    cmds:
      - "@remote echo '💾 Tworzenie backupu...' && echo ''"
      - "@remote BACKUP_FILE=/root/backup-$(date +%Y%m%d-%H%M%S).tar.gz && tar czf $BACKUP_FILE -C / etc/containers/systemd home/tom/sandbox/deploy home/tom/sandbox/letsencrypt 2>/dev/null && echo \"   ✅ Backup: $BACKUP_FILE\" || echo '   ❌ Backup failed'"
      - "@remote echo '' && echo '💡 Przywracanie: tar xzf backup-YYYYMMDD-HHMMSS.tar.gz -C /'"

  watch:
    desc: Continuous monitoring (5s interval)
    env: [staging, prod]
    cmds:
      - "@remote echo '📡 Monitoring usług (Ctrl+C aby zatrzymać)' && echo ''"
      - '@remote while true; do clear; date; echo ""; podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null; echo ""; systemctl is-active traefik web landing 2>/dev/null | paste - - -; echo ""; sleep 5; done'

  alert:
    desc: Check services and send alert if down
    env: [staging, prod]
    cmds:
      - "@remote echo '🔔 Sprawdzanie usług...'"
      - "@remote curl -sf http://localhost:8000/health > /dev/null && echo '   ✅ Web OK' || echo '🚨 ALERT: Web DOWN'"
      - "@remote curl -sf http://localhost:3000/ > /dev/null && echo '   ✅ Landing OK' || echo '🚨 ALERT: Landing DOWN'"

  # ─── Code generation ────────────────────────────────
  #   taskfile run init       # inicjalizuj projekt
  #   taskfile run generate   # generuj kod

  init:
    desc: Initialize project (dirs, venv, prompts)
    script: scripts/init.sh

  generate:
    desc: Generate code via Aider (web, desktop, landing)
    script: scripts/generate.sh

  # ─── Sync ──────────────────────────────────────────────
  #   taskfile run sync-check    # sprawdź czy zsynchronizowane
  #   taskfile run sync-readme   # synchronizuj

  sync-readme:
    desc: Sync sandbox files → README.md markpact blocks
    cmds:
      - markpact sync ../README.md --exclude .env

  sync-check:
    desc: Check if sandbox files are in sync with README.md
    cmds:
      - markpact sync ../README.md --exclude .env --check
```

### scripts/ — skrypty specyficzne dla projektu

> **Uwaga:** Skrypty deploymentu (`doctor.sh`, `setup-env.sh`, `setup-hosts.sh`,
> `setup-prod.sh`, `deploy.sh`, `clean.sh`) zostały usunięte — ich funkcjonalność
> jest teraz wbudowana w `taskfile` CLI (`taskfile doctor`, `taskfile setup prod`, itd.).

```markpact:file path=scripts/generate.sh
#!/usr/bin/env bash
set -euo pipefail

# Shared helper: load .env and find aider binary
load_env() {
  [ -f .env ] && export $(grep -v '^#' .env | xargs) 2>/dev/null || true
}

find_aider() {
  if [ -f .venv/bin/aider ]; then
    echo ".venv/bin/aider"
  elif command -v aider >/dev/null 2>&1; then
    echo "aider"
  else
    echo "❌ Aider nie zainstalowany. Uruchom: taskfile init" >&2
    echo "   Lub zainstaluj globalnie: pipx install aider-chat" >&2
    exit 1
  fi
}

run_aider() {
  local APP_DIR="$1"
  local PROMPT_FILE="$2"
  local AIDER
  AIDER=$(find_aider)
  echo "🤖 ${APP_DIR}... (używam: $AIDER)"
  cd "apps/${APP_DIR}" && $AIDER \
    --model "${AIDER_MODEL}" --openai-api-key "${OPENROUTER_API_KEY}" \
    --openai-api-base "https://openrouter.ai/api/v1" \
    --yes --no-git --message "$(cat "../../prompts/${PROMPT_FILE}")"
}

# === Main ===
load_env

COMPONENT="${1:-all}"

case "$COMPONENT" in
  web)
    run_aider "web" "web.md"
    ;;
  desktop)
    run_aider "desktop" "desktop.md"
    ;;
  landing)
    run_aider "landing" "landing.md"
    ;;
  all)
    [ -z "${OPENROUTER_API_KEY:-}" ] && echo "❌ Brak OPENROUTER_API_KEY w .env" && exit 1
    # Auto-init if apps/ don't exist
    if [ ! -d apps/web ] || [ ! -d apps/desktop ] || [ ! -d apps/landing ]; then
      echo "⚠️  Brak struktury apps/ - uruchamiam init..."
      taskfile init
    fi
    run_aider "web" "web.md"
    cd ../..
    run_aider "desktop" "desktop.md"
    cd ../..
    run_aider "landing" "landing.md"
    echo "📢 Kod wygenerowany"
    ;;
  *)
    echo "Użycie: $0 [web|desktop|landing|all]"
    exit 1
    ;;
esac
```

```markpact:file path=scripts/init.sh
#!/usr/bin/env bash
set -euo pipefail

# Tworzenie struktury katalogów
mkdir -p apps/web/templates apps/web/static apps/web/tests apps/desktop apps/landing prompts

# Virtualenv i zależności
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
echo "📦 Instaluję zależności Python..."
.venv/bin/pip install fastapi uvicorn jinja2 python-multipart pytest httpx 2>&1 | tail -3
echo ""
echo "📦 Próbuję zainstalować aider-chat..."
if .venv/bin/pip install aider-chat 2>&1 | tail -5; then
  echo "✅ Aider zainstalowany"
else
  echo ""
  echo "⚠️  Automatyczna instalacja aider nie powiodła się (problem z Python 3.13)"
  echo ""
  echo "   🔧 Rozwiązania:"
  echo "      1. Użyj pipx: pipx install aider-chat"
  echo "      2. Użyj starszego Pythona: python3.11 -m venv .venv"
  echo "      3. Ręcznie: .venv/bin/pip install 'aider-chat<0.50'"
  echo ""
  echo "   Jeśli aider jest zainstalowany globalnie, task generate użyje go."
  echo ""
fi

# Domyślne prompty
[ -f prompts/web.md ] || printf '%s\n' \
  "# Generate: SaaS Web Application (FastAPI)" "" \
  "Create a FastAPI web application in apps/web/ with:" "" \
  "## Files to create:" \
  "1. main.py - FastAPI app with health endpoint" \
  "2. templates/dashboard.html - Modern dashboard" \
  "3. requirements.txt - fastapi, uvicorn, jinja2" \
  "4. Dockerfile - python:3.12-slim" > prompts/web.md

[ -f prompts/desktop.md ] || printf '%s\n' \
  "# Generate: Desktop Application (Electron)" "" \
  "Create an Electron desktop app in apps/desktop/ with:" "" \
  "## Files to create:" \
  "1. package.json - Electron config" \
  "2. main.js - Main process" \
  "3. index.html - Renderer" > prompts/desktop.md

[ -f prompts/landing.md ] || printf '%s\n' \
  "# Generate: Landing Page" "" \
  "Create a static landing page in apps/landing/ with:" "" \
  "## Files to create:" \
  "1. index.html - Single page with TailwindCSS" \
  "2. Dockerfile - nginx:alpine" > prompts/landing.md

echo "✅ Gotowe! Następne: taskfile setup hosts"
```

### VERSION — wersja projektu

```markpact:file path=VERSION
1.0.0
```

### Pliki konfiguracyjne .env

Projekt używa **trzech plików .env** dla różnych środowisk:

| Plik | Środowisko | Zawartość |
|------|-----------|-----------|
| `.env` | Lokalne | Porty, klucze API, ustawienia dev |
| `.env.staging` | Staging | Domeny, hosty, certyfikaty staging |
| `.env.prod` | Produkcja | Domeny produkcyjne, hosty, certyfikaty |

#### `.env` — konfiguracja lokalna

```markpact:file path=.env
# Auto-generated by taskfile init

DOMAIN=localhost
OPENROUTER_API_KEY=sk-or-v1-
PROD_USER=root
STAGING_USER=root

PROJECT_NAME=taskfile-example
VERSION=1.0.0

# LLM Configuration
LLM_MODEL=openrouter/openrouter/moonshotai/kimi-k2.5
LLM_AGENT=aider

# Build
TAG=latest

# Ports
PORT_WEB=8001
PORT_LANDING=3001

# Hosts
STAGING_HOST=c2005.mask.services
PROD_HOST=c2006.mask.services
DEPLOY_USER=root
REGISTRY=ghcr.io/your-org

# Domains
DOMAIN_WEB=c2006.mask.services
DOMAIN_LANDING=c2007.mask.services
DOMAIN_API=api.c2006.mask.services

# Traefik TLS domains
WEB_DOMAIN=c2006.mask.services
LANDING_DOMAIN=c2007.mask.services
ACME_EMAIL=admin@softreck.com
```

#### `.env.staging` — konfiguracja staging

Tworzony ręcznie lub przez `taskfile setup hosts`:

```bash
# Staging environment
OPENROUTER_API_KEY=...
LLM_MODEL=openrouter/anthropic/claude-sonnet-4
LLM_AGENT=opencode
TAG=latest

STAGING_HOST=staging.example.com
DEPLOY_USER=deploy

DOMAIN_WEB=app-staging.example.com
DOMAIN_LANDING=staging.example.com
DOMAIN_API=api-staging.example.com
```

#### `.env.prod` — konfiguracja produkcji

Tworzony ręcznie lub przez `taskfile setup hosts`:

```bash
# Production environment
OPENROUTER_API_KEY=...
LLM_MODEL=openrouter/anthropic/claude-sonnet-4
LLM_AGENT=opencode
TAG=latest

PROD_HOST=prod.example.com
DEPLOY_USER=deploy

DOMAIN_WEB=app.example.com
DOMAIN_LANDING=example.com
DOMAIN_API=api.example.com
```

### .gitignore — ignorowane pliki

```markpact:file path=.gitignore
# Environment files
!.env
.env.local
.env.prod
.env.staging

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/
.pytest_cache/

# Node
node_modules/
dist/
build/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db
```

### prompts/ — prompty dla Aidera

```markpact:file path=prompts/web.md
# Generate: SaaS Web Application (FastAPI)

Create FastAPI app in apps/web/:

1. main.py - FastAPI with /health, /api/v1/status, /dashboard
2. templates/dashboard.html - TailwindCSS dashboard
3. templates/login.html - Login form
4. requirements.txt - fastapi, uvicorn, jinja2
5. Dockerfile - python:3.12-slim, port 8000
6. tests/test_app.py - pytest tests

Tech: FastAPI + Uvicorn + Jinja2 + TailwindCSS CDN
```

```markpact:file path=prompts/desktop.md
# Generate: Desktop Application (Electron)

Create Electron app in apps/desktop/:

1. package.json - Electron 28+, electron-builder
2. main.js - Main process, BrowserWindow, system tray
3. preload.js - contextBridge
4. index.html - Renderer with API status

Features: Cross-platform, system tray, TailwindCSS
```

```markpact:file path=prompts/landing.md
# Generate: Landing Page

Create static landing page in apps/landing/:

1. index.html - Hero, CTA, How It Works, Download, Pricing
2. Dockerfile - nginx:alpine, port 80

Tech: Static HTML + TailwindCSS CDN + Nginx
```

### docker-compose.yml — konfiguracja Docker

```markpact:file path=docker-compose.yml
services:
  web:
    build: ./apps/web
    ports:
      - "${PORT_WEB:-8000}:8000"
    environment:
      - VERSION=${VERSION:-1.0.0}

  landing:
    build: ./apps/landing
    ports:
      - "${PORT_LANDING:-3000}:80"
```

### deploy/quadlet/ — Podman Quadlet units (systemd)

```markpact:file path=deploy/quadlet/web.container
[Unit]
Description=web container
After=network.target

[Container]
ContainerName=web
Image=docker.io/library/sandbox-web:latest
Environment=VERSION=1.0.0
PublishPort=8000:8000
Network=host

[Service]
Restart=always
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target default.target
```

```markpact:file path=deploy/quadlet/landing.container
[Unit]
Description=landing container
After=network.target

[Container]
ContainerName=landing
Image=docker.io/library/sandbox-landing:latest
PublishPort=3000:3000
Network=host

[Service]
Restart=always
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target default.target
```

```markpact:file path=deploy/quadlet/proxy.network
[Network]
NetworkName=proxy
Driver=bridge
DNSEnabled=false
```

```markpact:file path=deploy/quadlet/traefik.container
[Unit]
Description=Traefik reverse proxy with TLS
After=network.target

[Container]
ContainerName=traefik
Image=docker.io/traefik:v3.0
PublishPort=80:80
PublishPort=443:443
PublishPort=8080:8080
Network=host
Volume=/home/tom/sandbox/deploy/traefik.yml:/etc/traefik/traefik.yml:ro
Volume=/home/tom/sandbox/deploy/traefik-dynamic.yml:/etc/traefik/dynamic/traefik-dynamic.yml:ro
Volume=/home/tom/sandbox/letsencrypt:/letsencrypt

[Service]
Restart=always
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target default.target
```

### deploy/ — Traefik configuration

```markpact:file path=deploy/resolv.conf
search dns.podman
nameserver 8.8.8.8
nameserver 1.1.1.1
```

```markpact:file path=deploy/traefik.yml
global:
  checkNewVersion: false
  sendAnonymousUsage: false

api:
  dashboard: true

log:
  level: INFO

providers:
  file:
    directory: /etc/traefik/dynamic
    watch: true

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@softreck.com
      storage: /letsencrypt/acme.json
      tlsChallenge: {}
```

```markpact:file path=deploy/traefik-dynamic.yml
http:
  routers:
    web:
      rule: "Host(`c2006.mask.services`)"
      entryPoints:
        - "websecure"
      service: "web"
      tls:
        certResolver: "letsencrypt"

    landing:
      rule: "Host(`c2007.mask.services`)"
      entryPoints:
        - "websecure"
      service: "landing"
      tls:
        certResolver: "letsencrypt"

  services:
    web:
      loadBalancer:
        servers:
          - url: "http://localhost:8000"

    landing:
      loadBalancer:
        servers:
          - url: "http://localhost:3000"
```

```markpact:file path=Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy application code
COPY . .

# Default port
ENV MARKPACT_PORT=8000
EXPOSE 8000

CMD ["python", "-m", "http.server", "8000"]
```

---

## 📚 Dokumentacja Taskfile

```bash
# Komendy wbudowane (CLI)
taskfile init                   # Interaktywne tworzenie Taskfile
taskfile list                   # Lista tasków
taskfile doctor                 # Diagnostyka projektu
taskfile validate               # Walidacja Taskfile.yml

# Uruchamianie tasków
taskfile run <task>             # Uruchom task
taskfile run deploy --env prod  # Task z wybranym środowiskiem
taskfile --dry-run run deploy   # Podgląd komend bez wykonania

# Dodatkowe
taskfile watch build            # Watch mode
taskfile serve                  # Web UI
taskfile cache show             # Cache stats
```

## 🎯 Zalety Single-File Project

1. **Jeden plik źródłowy** — cały projekt w README.md
2. **Markpact standard** — używa ogólnodostępnego narzędzia
3. **Taskfile zarządza** — wszystkie operacje w jednym miejscu
4. **Łatwe wersjonowanie** — zmiana w README = zmiana projektu
5. **Proste dzielenie** — wystarczy przesłać jeden plik

## 🔮 Rozszerzenia

### Konfiguracja Traefik (Reverse Proxy + SSL)

Traefik jest domyślnie skonfigurowany z automatycznym TLS via Let's Encrypt.

**Wymagana konfiguracja w `.env`:**
```bash
WEB_DOMAIN=web.twojadomena.com
LANDING_DOMAIN=landing.twojadomena.com
ACME_EMAIL=admin@twojadomena.com
```

**Dashboard Traefik:**
- Dostępny na porcie 8080 (np. `http://twoj-serwer:8080`)

**Ręczne zarządzanie certyfikatami:**
```bash
# Na serwerze produkcyjnym
ssh root@twoj-serwer 'cat /home/tom/sandbox/letsencrypt/acme.json'
```

---

## 📝 Wnioski — jak unikać problemów z IaC i Taskfile

### Napotkane problemy i ich przyczyny

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|-------------|
| `2>&1` traktowane jako argument | `shlex.split` quotuje shell redirects | Upgrade taskfile CLI (fix w 0.3.76) |
| `${COMPOSE}` not found w doctor | Brak rozwiązywania zmiennych przed sprawdzeniem binarki | Fix w `check_task_commands` — resolve vars z `config.variables` |
| DNS timeout w kontenerze | Podman bridge DNS (10.89.0.1) nie rozwiązuje zewn. domen | Mount `resolv.conf` z publicznym DNS (8.8.8.8) |
| UFW blokuje ruch kontenerów | `DEFAULT_FORWARD_POLICY=DROP` blokuje podman subnet | `ufw route allow` dla podman1 ↔ ens6 |
| `${ACME_EMAIL}` w traefik.yml | Traefik nie rozwiązuje zmiennych shellowych | Hardcode email w pliku YAML |
| `for/do/done` w komendach | `shlex.split` rozbija shell loops | Uprość do `cmd && echo OK \|\| echo FAIL` |
| Restart gubi port mappings | Podman quadlet race condition przy szybkim restart | `systemctl stop; sleep 3; systemctl start` |

### Jak poprawić taskfile CLI, aby zapobiegać tym problemom

#### 1. **Pre-deploy validation** (`taskfile doctor --pre-deploy`)
Przed każdym `deploy` automatycznie sprawdzaj:
- DNS z kontenera (czy ACME będzie działać)
- Firewall FORWARD chain (czy kontenery mają internet)
- Poprawność quadlet files (syntax, volumes exist)
- Dostępność portów na hoście

#### 2. **Automatyczny DNS w generatorze quadlet**
Gdy taskfile generuje pliki `.container`, automatycznie dodawaj:
```ini
Volume=/path/to/resolv.conf:/etc/resolv.conf:ro
```
i twórz `resolv.conf` z publicznym DNS, jeśli wykryje podman bridge network.

#### 3. **Shell-safe command mode**
Zamiast parsować komendy przez `shlex.split` (co łamie `for/do/done`, `if/then/fi`, `(...)`),
przekazuj je bezpośrednio do `sh -c` bez glob expansion:
```python
# Gdy komenda zawiera shell constructs → skip glob expansion
if any(kw in cmd for kw in ('for ', 'while ', 'if ', '(', ')')):
    subprocess.run(['sh', '-c', cmd])  # pass-through
```

#### 4. **Traefik config linting**
W `taskfile doctor` sprawdzaj pliki Traefik pod kątem:
- `${VAR}` w YAML (Traefik ich nie rozwiązuje → błąd)
- Brak `email:` w ACME config
- Domeny z `example.com` (placeholder nie zmieniony)

#### 5. **Graceful restart w taskach**
Zamiast `systemctl restart` (race condition z portami), domyślnie używaj:
```yaml
- "@remote systemctl stop traefik && sleep 3 && systemctl start traefik"
```

#### 6. **IaC best practices w Taskfile**
- **Nie używaj `${VAR}` w plikach YAML** które nie są przetwarzane przez shell (traefik, k8s)
- **Unikaj `for/while/if`** w komendach Taskfile — rozbij na proste `cmd && ok || fail`
- **Testuj z `--dry-run`** przed każdym deploy na prod
- **`taskfile doctor --remote`** po każdym deploy — weryfikuj stan serwera
- **Backup przed zmianami**: `taskfile --env prod run backup`

### Rekomendowana kolejność operacji (IaC workflow)

```bash
# 1. Walidacja lokalna
taskfile validate
taskfile doctor

# 2. Build i test
taskfile run build
taskfile run dev
taskfile --env local run health

# 3. Pre-deploy check
taskfile --env prod doctor --remote

# 4. Deploy
taskfile --env prod run deploy

# 5. Post-deploy verification
taskfile --env prod run health
taskfile --env prod run logs

# 6. Jeśli problem → rollback
taskfile --env prod run rollback
```

---

## 👤 Autor

**Tom Sapletta** — tom@sapletta.com

**Licencja:** MIT
