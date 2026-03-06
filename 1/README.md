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
    ├── .env               → Konfiguracja (hosty, klucze, porty)
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
```

### Build i deploy

```bash
# Build obrazów Docker
taskfile run build

# Deploy lokalny (docker compose up -d)
taskfile run deploy

# Transfer obrazów na serwer (bez registry!)
taskfile push sandbox-web:latest sandbox-landing:latest

# Deploy na prod (SSH → podman)
taskfile --env prod run deploy

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

## 🔧 Dostępne komendy

### Taski projektowe (z Taskfile.yml)

| Komenda | Opis |
|---------|------|
| `taskfile run init` | Tworzy strukturę katalogów, instaluje zależności |
| `taskfile run generate` | Generuje kod przez Aider (web, desktop, landing) |
| `taskfile run build` | Build Docker images |
| `taskfile run deploy` | Deploy (`@local` compose / `@remote` quadlet) |
| `taskfile run dev` | Start lokalny z hot-reload |
| `taskfile run stop` | Stop serwisów (`@local`/`@remote`) |
| `taskfile run logs` | Logi (`@local`/`@remote`) |
| `taskfile run status` | Status serwisów (`@local`/`@remote`) |

### Wbudowane komendy CLI (nie wymagają Taskfile.yml)

| Komenda | Opis |
|---------|------|
| `taskfile doctor` | 🔧 5-warstwowa diagnostyka (preflight, validation, env, fix, LLM) |
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
name: my-app
description: Example Taskfile — local Docker Compose + remote Podman deploy

variables:
  APP_NAME: sandbox
  TAG: latest
  WEB_IMAGE: sandbox-web
  LANDING_IMAGE: sandbox-landing
  COMPOSE: docker compose

environments:
  local:
    container_runtime: docker
    compose_command: docker compose

  prod:
    ssh_host: ${PROD_HOST:-your-server.example.com}
    ssh_user: ${DEPLOY_USER:-root}
    container_runtime: podman

tasks:
  # ─── Core tasks ───────────────────────────────────────

  build:
    desc: Build Docker images locally
    cmds:
      - ${COMPOSE} build

  deploy:
    desc: Deploy to target environment
    env: [local, prod]
    deps: [build]
    cmds:
      - "@local ${COMPOSE} up -d"
      - "@remote mkdir -p /etc/containers/systemd /home/tom/sandbox/deploy /home/tom/sandbox/letsencrypt"
      - "@remote scp deploy/quadlet/*.container deploy/quadlet/*.network deploy/traefik.yml deploy/traefik-dynamic.yml ${DEPLOY_USER}@${PROD_HOST}:/etc/containers/systemd/"
      - "@remote ssh ${DEPLOY_USER}@${PROD_HOST} 'systemctl daemon-reload && systemctl start traefik container-web container-landing'"

  # ─── Development ──────────────────────────────────────

  dev:
    desc: Start local dev with hot-reload
    env: [local]
    cmds:
      - ${COMPOSE} up -d --build
      - echo "✅ Dev running at http://localhost:${PORT_WEB:-8000}"
      - ${COMPOSE} logs -f

  # ─── Operations ───────────────────────────────────────

  stop:
    desc: Stop services
    env: [local, prod]
    cmds:
      - "@local ${COMPOSE} down"
      - "@remote podman stop ${WEB_IMAGE} ${LANDING_IMAGE} 2>/dev/null || true"
      - "@remote podman rm ${WEB_IMAGE} ${LANDING_IMAGE} 2>/dev/null || true"

  logs:
    desc: View logs
    env: [local, prod]
    cmds:
      - "@local ${COMPOSE} logs --tail 50"
      - "@remote echo '=== sandbox-web ===' && podman logs --tail 20 ${WEB_IMAGE} && echo '=== sandbox-landing ===' && podman logs --tail 20 ${LANDING_IMAGE}"

  status:
    desc: Show service status
    env: [local, prod]
    cmds:
      - "@local ${COMPOSE} ps"
      - "@remote podman ps --filter name=${WEB_IMAGE} --filter name=${LANDING_IMAGE}"

  # ─── Code generation (project-specific) ────────────────

  init:
    desc: Initialize project (dirs, venv, prompts)
    script: scripts/init.sh

  generate:
    desc: Generate code via Aider (web, desktop, landing)
    script: scripts/generate.sh

  # ─── Sync ──────────────────────────────────────────────

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
[ -f prompts/web.md ] || printf '%s
' \
  "# Generate: SaaS Web Application (FastAPI)" "" \
  "Create a FastAPI web application in apps/web/ with:" "" \
  "## Files to create:" \
  "1. main.py - FastAPI app with health endpoint" \
  "2. templates/dashboard.html - Modern dashboard" \
  "3. requirements.txt - fastapi, uvicorn, jinja2" \
  "4. Dockerfile - python:3.12-slim" > prompts/web.md

[ -f prompts/desktop.md ] || printf '%s
' \
  "# Generate: Desktop Application (Electron)" "" \
  "Create an Electron desktop app in apps/desktop/ with:" "" \
  "## Files to create:" \
  "1. package.json - Electron config" \
  "2. main.js - Main process" \
  "3. index.html - Renderer" > prompts/desktop.md

[ -f prompts/landing.md ] || printf '%s
' \
  "# Generate: Landing Page" "" \
  "Create a static landing page in apps/landing/ with:" "" \
  "## Files to create:" \
  "1. index.html - Single page with TailwindCSS" \
  "2. Dockerfile - nginx:alpine" > prompts/landing.md

echo "✅ Gotowe! Następne: taskfile setup hosts"
```

### VERSION — wersja projektu

```markpact:file path=VERSION
0.1.1
```

### .env — zmienne środowiskowe

```markpact:file path=.env
PROJECT_NAME=taskfile-example
VERSION=1.0.0
OPENROUTER_API_KEY=
AIDER_MODEL=openrouter/anthropic/claude-sonnet-4
PORT_WEB=8000
PORT_LANDING=3000
STAGING_HOST=
PROD_HOST=
DEPLOY_USER=deploy
REGISTRY=ghcr.io/your-org

# Traefik TLS domains
WEB_DOMAIN=web.example.com
LANDING_DOMAIN=landing.example.com
ACME_EMAIL=admin@example.com
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

[Container]
ContainerName=web
Image=docker.io/library/sandbox-web:latest
Environment=VERSION=1.0.0
Network=proxy.network

[Service]
Restart=always
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target default.target
```

```markpact:file path=deploy/quadlet/landing.container
[Unit]
Description=landing container

[Container]
ContainerName=landing
Image=docker.io/library/sandbox-landing:latest
Network=proxy.network

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
Network=proxy.network
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
      email: ${ACME_EMAIL:-admin@example.com}
      storage: /letsencrypt/acme.json
      tlsChallenge: {}
```

```markpact:file path=deploy/traefik-dynamic.yml
http:
  routers:
    web:
      rule: "Host(`${WEB_DOMAIN:-web.example.com}`)"
      entryPoints:
        - "websecure"
      service: "web"
      tls:
        certResolver: "letsencrypt"

    landing:
      rule: "Host(`${LANDING_DOMAIN:-landing.example.com}`)"
      entryPoints:
        - "websecure"
      service: "landing"
      tls:
        certResolver: "letsencrypt"

  services:
    web:
      loadBalancer:
        servers:
          - url: "http://web:8000"

    landing:
      loadBalancer:
        servers:
          - url: "http://landing:80"
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

## 👤 Autor

**Tom Sapletta** — tom@sapletta.com

**Licencja:** MIT
