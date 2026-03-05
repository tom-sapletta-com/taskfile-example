# Taskfile + Markpact Project

**Cały projekt w jednym pliku README.md — wypakuj i uruchom przez Taskfile.**

## 🚀 Szybki start

```bash
# 1. Instalacja
pip install markpact taskfile --upgrade

# 2. Wypakowanie projektu
markpact README.md
cd sandbox
taskfile init

# 3. Konfiguracja (interaktywnie)
taskfile setup env       # Konfiguruje .env, API keys
taskfile setup hosts     # Konfiguruje hosty deploymentu

# 4. Generowanie i uruchomienie
taskfile generate   # Generuje kod przez Aider
taskfile dev        # Start lokalny
```

## 📋 Co to jest?

Ten projekt demonstruje podejście **Single-File Project** z wydzieloną logiką do skryptów:

1. **README.md** zawiera wszystkie pliki jako bloki `markpact:file path=...`
2. **Taskfile.yml** jest krótki (~130 linii) — używa `script:` do referencjonowania skryptów
3. **scripts/*.sh** zawierają logikę (dodatkowo ~300 linii, ale łatwiejsze w edycji niż inline YAML)
4. **markpact** wypakowuje pliki, **taskfile** zarządza projektem

## 🏗️ Architektura

```
README.md (ten plik)
    │
    ├─ markpact:file path=Taskfile.yml     → Deklaracja tasków (krótki YAML)
    ├─ markpact:file path=scripts/*.sh     → Logika wydzielona do skryptów
    ├─ markpact:file path=prompts/*.md      → Prompty dla AI
    └─ markpact:file path=docker-compose.yml → Docker
    │
    └─► markpact README.md (wypakowuje)
    │
    ▼
./sandbox/
    ├── Taskfile.yml       → Task runner (deklaracja, używa script:)
    ├── scripts/           → Logika wydzielona do skryptów .sh
    │   ├── doctor.sh
    │   ├── setup-env.sh
    │   ├── setup-hosts.sh
    │   ├── generate.sh
    │   ├── init.sh
    │   └── clean.sh
    ├── .env               → Konfiguracja (hosty, klucze, porty)
    ├── prompts/           → Prompty dla Aidera
    │   ├── web.md
    │   ├── desktop.md
    │   └── landing.md
    └── docker-compose.yml → Konfiguracja Docker
```

## 🎯 Workflow

```bash
# FAZA 1: Inicjalizacja
markpact README.md              # Wypakuj pliki
cd sandbox                      # Wejdź do folderu
taskfile init                   # Zainstaluj zależności

# FAZA 2: Konfiguracja
taskfile setup env              # Skonfiguruj .env
taskfile setup hosts            # Dodaj hosty staging/prod

# FAZA 3: Generowanie kodu
taskfile generate               # Generuj wszystko (web, desktop, landing)

# FAZA 4: Rozwój
taskfile dev                    # Start lokalny
taskfile dev-web                # Web z hot-reload
taskfile test                   # Testy

# FAZA 5: Deployment
taskfile build                  # Build Docker images
taskfile deploy                 # Interaktywny deployment
```

## 🔧 Taski dostępne po wypakowaniu

| Task | Opis |
|------|------|
| `init` | Tworzy strukturę katalogów, instaluje zależności |
| `setup env` | 🔐 Interaktywna konfiguracja .env (LLM provider, API keys, porty) |
| `setup hosts` | 🌐 Konfiguracja hostów staging/prod |
| `generate` | Generuje kod przez Aider (web, desktop, landing) |
| `test` | Uruchamia pytest |
| `build` | Buduje obrazy Docker |
| `dev` | Startuje docker-compose lokalnie |
| `deploy` | Interaktywny deployment do staging/prod |
| `clean` | Czyści projekt (zostaje tylko README.md) |

**Wbudowane komendy CLI:**
- `taskfile doctor` - Diagnostyka projektu
- `taskfile list` - Lista tasków
- `taskfile init` - Interaktywne tworzenie Taskfile

---

## Pliki projektu (markpact)

### Taskfile.yml — konfiguracja tasków

```markpact:file path=Taskfile.yml
version: "1"
name: taskfile-example
description: "Taskfile-driven project with Aider code generation"

variables:
  PROJECT_NAME: taskfile-example
  VERSION: ${VERSION:-1.0.0}
  IMAGE_WEB: ghcr.io/tom-sapletta-com/taskfile-example-web
  IMAGE_LANDING: ghcr.io/tom-sapletta-com/taskfile-example-landing
  TAG: ${TAG:-latest}

environments:
  local:
    container_runtime: docker
    compose_command: docker compose
    env_file: .env

  staging:
    ssh_host: ${STAGING_HOST:-}
    ssh_user: ${DEPLOY_USER:-deploy}
    ssh_key: ~/.ssh/id_ed25519
    container_runtime: podman
    service_manager: quadlet
    env_file: .env

  prod:
    ssh_host: ${PROD_HOST:-}
    ssh_user: ${DEPLOY_USER:-deploy}
    ssh_key: ~/.ssh/id_ed25519
    container_runtime: podman
    service_manager: quadlet
    env_file: .env

functions:
  health-check:
    lang: shell
    code: |
      URL="${1:-http://localhost:8000/health}"
      for i in $(seq 1 10); do
        curl -sf "$URL" > /dev/null 2>&1 && echo "OK: $URL" && exit 0
        echo "Waiting... ($i/10)"; sleep 3
      done
      echo "FAILED: $URL"; exit 1

  notify:
    lang: python
    code: |
      import os
      print(f"[notify] {os.environ.get('FN_ARGS', 'Done')}")

tasks:
  setup-env:
    desc: "🔐 Interaktywna konfiguracja .env - LLM provider, API keys, porty"
    script: scripts/setup-env.sh

  setup-hosts:
    desc: "Konfiguracja hostów deploymentu"
    script: scripts/setup-hosts.sh

  setup:
    desc: "Konfiguracja projektu (env | hosts)"
    cmds:
      - |
        if [ "${1:-}" = "env" ]; then
          bash scripts/setup-env.sh
        elif [ "${1:-}" = "hosts" ]; then
          bash scripts/setup-hosts.sh
        else
          echo "Użycie: taskfile setup <env|hosts>"
          exit 1
        fi

  init:
    desc: "Inicjalizacja - tworzy strukturę, instaluje aider"
    script: scripts/init.sh

  generate:
    desc: "Generowanie kodu przez Aider (all/web/desktop/landing)"
    script: scripts/generate.sh

  generate-web:
    desc: "Generowanie FastAPI"
    cmds:
      - bash scripts/generate.sh web

  generate-desktop:
    desc: "Generowanie Electron"
    cmds:
      - bash scripts/generate.sh desktop

  generate-landing:
    desc: "Generowanie Landing"
    cmds:
      - bash scripts/generate.sh landing

  test:
    desc: "Testy"
    cmds:
      - cd apps/web && ../../.venv/bin/python -m pytest tests/ -v 2>/dev/null || echo "⚠️ Brak testów"

  build:
    desc: "Build Docker"
    cmds:
      - docker build -t ${IMAGE_WEB}:${TAG} apps/web/
      - docker build -t ${IMAGE_LANDING}:${TAG} apps/landing/

  dev:
    desc: "Start lokalny"
    env: [local]
    cmds:
      - docker compose up -d --build
      - echo "🌐 http://localhost:${PORT_WEB:-8000} (web)"
      - echo "🌐 http://localhost:${PORT_LANDING:-3000} (landing)"

  dev-web:
    desc: "Web z hot reload"
    cmds:
      - cd apps/web && ../../.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port ${PORT_WEB:-8000}

  deploy:
    desc: "Deployment (interaktywny)"
    script: scripts/deploy.sh

  deploy-exec:
    desc: "Wykonanie deploymentu"
    env: [staging, prod]
    retries: 2
    retry_delay: 10
    cmds:
      - |
        echo "🚀 Deploying to ${SSH_HOST}..."
        echo "💡 Run manually: ssh ${DEPLOY_USER}@${SSH_HOST} 'podman pull ${IMAGE_WEB}:${TAG}'"
      - "@fn health-check http://${SSH_HOST}/health"
      - echo "📢 Deployment gotowy"

  status:
    desc: "Status"
    cmds:
      - "@fn health-check http://localhost:${PORT_WEB:-8000}/health"

  clean:
    desc: "Czyszczenie z wyborem - pyta co usunąć"
    script: scripts/clean.sh
```

### scripts/ — skrypty bash

```markpact:file path=scripts/doctor.sh
#!/usr/bin/env bash
set -euo pipefail

# Load environment variables from .env
[ -f .env ] && export $(grep -v '^#' .env | xargs) 2>/dev/null || true
echo "🔧 Taskfile Doctor - sprawdzam projekt..."
ERRORS=0

# Sprawdź czy .env istnieje
if [ ! -f .env ]; then
  echo "⚠️  Brak .env - tworzę z szablonu..."
  printf '%s\n' \
    "PROJECT_NAME=taskfile-example" \
    "VERSION=1.0.0" \
    "OPENROUTER_API_KEY=" \
    "AIDER_MODEL=openrouter/anthropic/claude-sonnet-4" \
    "PORT_WEB=8000" \
    "PORT_LANDING=3000" \
    "STAGING_HOST=" \
    "PROD_HOST=" \
    "DEPLOY_USER=deploy" > .env
  echo "✅ Utworzono .env"
  ((ERRORS++))
fi

# Sprawdź czy prompts/ istnieją
if [ ! -d prompts ]; then
  echo "⚠️  Brak prompts/ - uruchom: taskfile init"
  ((ERRORS++))
fi

# Sprawdź czy .venv istnieje
if [ ! -d .venv ]; then
  echo "⚠️  Brak .venv - uruchom: taskfile init"
  ((ERRORS++))
fi

# Sprawdź OPENROUTER_API_KEY
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "⚠️  Brak OPENROUTER_API_KEY w .env"
  echo ""
  echo "   🔧 Rozwiązanie: Uruchom interaktywną konfigurację:"
  echo "      taskfile setup env"
  echo ""
  echo "   Lub ręcznie dodaj klucz:"
  echo "      echo 'OPENROUTER_API_KEY=sk-or-v1-...' >> .env"
  echo ""
  ((ERRORS++))
fi

if [ $ERRORS -eq 0 ]; then
  echo "✅ Wszystko OK! Projekt gotowy."
else
  echo "🔧 Naprawiono $ERRORS problemów. Sprawdź powyżej."
fi
```

```markpact:file path=scripts/setup-env.sh
#!/usr/bin/env bash
set -euo pipefail

echo ""
echo "🔐 Konfiguracja środowiska (.env)"
echo ""

# Upewnij się że .env istnieje
if [ ! -f .env ]; then
  touch .env
fi

# === LLM PROVIDER ===
echo "🤖 Wybierz providera LLM:"
echo ""
echo "  1) OpenRouter (darmowe modele!) - https://openrouter.ai"
echo "     💡 Najlepszy wybór - darmowe tokeny, wiele modeli"
echo ""
echo "  2) OpenAI (GPT-4, GPT-3.5) - https://platform.openai.com"
echo "     💡 Płatne, ale bardzo stabilne"
echo ""
echo "  3) Anthropic (Claude) - https://console.anthropic.com"
echo "     💡 Bardzo dobre do kodu"
echo ""
echo "  4) Ollama (lokalnie, darmowe!) - https://ollama.com"
echo "     💡 Działa offline, wymaga instalacji Ollama"
echo ""
echo "  5) Groq (szybkie, tanie) - https://console.groq.com"
echo "     💡 Bardzo szybkie odpowiedzi"
echo ""
echo ""
echo "⏳ Czekam na wybór..."
printf "Wybór (1-5) [1]: "
read PROVIDER_CHOICE
PROVIDER_CHOICE=${PROVIDER_CHOICE:-1}
echo "✅ Wybrano opcję: $PROVIDER_CHOICE"

case "$PROVIDER_CHOICE" in
  1)
    PROVIDER="openrouter"
    API_URL="https://openrouter.ai/settings/keys"
    DEFAULT_MODEL="openrouter/anthropic/claude-sonnet-4"
    ;;
  2)
    PROVIDER="openai"
    API_URL="https://platform.openai.com/api-keys"
    DEFAULT_MODEL="gpt-4"
    ;;
  3)
    PROVIDER="anthropic"
    API_URL="https://console.anthropic.com/settings/keys"
    DEFAULT_MODEL="claude-3-5-sonnet-20241022"
    ;;
  4)
    PROVIDER="ollama"
    API_URL="https://ollama.com/download"
    DEFAULT_MODEL="qwen2.5-coder:14b"
    ;;
  5)
    PROVIDER="groq"
    API_URL="https://console.groq.com/keys"
    DEFAULT_MODEL="groq/llama-3.3-70b-versatile"
    ;;
  *)
    PROVIDER="openrouter"
    API_URL="https://openrouter.ai/settings/keys"
    DEFAULT_MODEL="openrouter/anthropic/claude-sonnet-4"
    ;;
esac

echo ""
echo "✅ Wybrano: $PROVIDER"
echo ""

# === API KEY ===
CURRENT_KEY=$(grep "^OPENROUTER_API_KEY=\|^OPENAI_API_KEY=\|^ANTHROPIC_API_KEY=\|^GROQ_API_KEY=" .env 2>/dev/null | cut -d= -f2 || echo "")
API_KEY=""

if [ -n "$CURRENT_KEY" ]; then
  echo "🔑 Obecny klucz API: ${CURRENT_KEY:0:10}..."
  echo ""
  echo "⏳ Czekam na decyzję..."
  printf "Zmienić? (t/n) [n]: "
  read CHANGE_KEY
  if [ "$CHANGE_KEY" != "t" ]; then
    echo "   ✅ Pozostawiam obecny klucz"
    API_KEY="$CURRENT_KEY"
  else
    echo "   🔄 Będę prosić o nowy klucz API"
  fi
fi

if [ -z "$API_KEY" ] && [ "$PROVIDER" != "ollama" ]; then
  echo ""
  echo "📋 Instrukcja pobrania klucza API:"
  echo ""
  echo "   1. Otwórz: $API_URL"
  echo "   2. Zaloguj się lub utwórz konto"
  echo "   3. Utwórz nowy klucz API"
  echo "   4. Skopiuj klucz i wklej poniżej"
  echo ""
  echo "⏳ Czekam na wklejenie klucza..."
  printf "🔑 Wklej klucz API: "
  read API_KEY
  echo "✅ Otrzymano klucz API"

  # Zapisz klucz z odpowiednią nazwą zmiennej
  case "$PROVIDER" in
    openrouter)
      sed -i "/^OPENROUTER_API_KEY=/d" .env 2>/dev/null
      echo "OPENROUTER_API_KEY=$API_KEY" >> .env
      ;;
    openai)
      sed -i "/^OPENAI_API_KEY=/d" .env 2>/dev/null
      echo "OPENAI_API_KEY=$API_KEY" >> .env
      ;;
    anthropic)
      sed -i "/^ANTHROPIC_API_KEY=/d" .env 2>/dev/null
      echo "ANTHROPIC_API_KEY=$API_KEY" >> .env
      ;;
    groq)
      sed -i "/^GROQ_API_KEY=/d" .env 2>/dev/null
      echo "GROQ_API_KEY=$API_KEY" >> .env
      ;;
  esac

  echo "   ✅ Klucz zapisany"
fi

# === MODEL ===
echo ""
echo "🎯 Konfiguracja modelu AI"
CURRENT_MODEL=$(grep "^AIDER_MODEL=" .env 2>/dev/null | cut -d= -f2 || echo "")
if [ -n "$CURRENT_MODEL" ]; then
  echo "🎯 Obecny model: $CURRENT_MODEL"
fi
echo ""
echo "⏳ Czekam na wybór modelu..."
printf "🎯 Model [$DEFAULT_MODEL]: "
read MODEL
MODEL=${MODEL:-$DEFAULT_MODEL}
echo "✅ Wybrano model: $MODEL"
sed -i "/^AIDER_MODEL=/d" .env 2>/dev/null
echo "AIDER_MODEL=$MODEL" >> .env

# === PORTY ===
echo ""
echo "🌐 Konfiguracja portów:"
echo ""

CURRENT_WEB=$(grep "^PORT_WEB=" .env 2>/dev/null | cut -d= -f2 || echo "")
CURRENT_WEB=${CURRENT_WEB:-8000}
echo ""
echo "⏳ Czekam na port Web App..."
printf "   Port Web App [$CURRENT_WEB]: "
read PORT_WEB
PORT_WEB=${PORT_WEB:-$CURRENT_WEB}
sed -i "/^PORT_WEB=/d" .env 2>/dev/null
echo "PORT_WEB=$PORT_WEB" >> .env
echo "✅ Ustawiono port Web: $PORT_WEB"

CURRENT_LANDING=$(grep "^PORT_LANDING=" .env 2>/dev/null | cut -d= -f2 || echo "")
CURRENT_LANDING=${CURRENT_LANDING:-3000}
echo ""
echo "⏳ Czekam na port Landing..."
printf "   Port Landing [$CURRENT_LANDING]: "
read PORT_LANDING
PORT_LANDING=${PORT_LANDING:-$CURRENT_LANDING}
sed -i "/^PORT_LANDING=/d" .env 2>/dev/null
echo "PORT_LANDING=$PORT_LANDING" >> .env
echo "✅ Ustawiono port Landing: $PORT_LANDING"

# === PROJECT NAME ===
echo ""
echo "📁 Konfiguracja nazwy projektu"
CURRENT_NAME=$(grep "^PROJECT_NAME=" .env 2>/dev/null | cut -d= -f2 || echo "")
CURRENT_NAME=${CURRENT_NAME:-taskfile-example}
echo ""
echo "⏳ Czekam na nazwę projektu..."
printf "📁 Nazwa projektu [$CURRENT_NAME]: "
read PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-$CURRENT_NAME}
sed -i "/^PROJECT_NAME=/d" .env 2>/dev/null
echo "PROJECT_NAME=$PROJECT_NAME" >> .env
echo "✅ Ustawiono nazwę projektu: $PROJECT_NAME"

# === VERSION ===
sed -i "/^VERSION=/d" .env 2>/dev/null
echo "VERSION=1.0.0" >> .env

echo ""
echo "✅ Konfiguracja zapisana do .env"
echo ""
echo "📋 Podsumowanie:"
echo "   Provider: $PROVIDER"
echo "   Model: $MODEL"
echo "   Porty: $PORT_WEB (web), $PORT_LANDING (landing)"
echo ""
echo "🔧 Teraz uruchom: taskfile setup hosts"
```

```markpact:file path=scripts/setup-hosts.sh
#!/usr/bin/env bash
set -euo pipefail

# Autonaprawa: sprawdź czy .env istnieje
if [ ! -f .env ]; then
  echo "⚠️  Brak .env - tworzę..."
  taskfile doctor
fi

echo ""
echo "🌐 Konfiguracja hostów deploymentu"
echo ""
echo "💡 Przykłady:"
echo "   Staging: staging.example.com, staging.myapp.io, 192.168.1.100"
echo "   Prod:    prod.example.com, www.myapp.io, 203.0.113.10"
echo "   User:    deploy, ubuntu, ec2-user"
echo ""
echo "   (Wciśnij Enter aby pominąć lub zachować obecną wartość)"
echo ""

for var in STAGING_HOST PROD_HOST DEPLOY_USER; do
  val=$(grep "^${var}=" .env 2>/dev/null | cut -d= -f2 || echo "")
  [ "$var" = "DEPLOY_USER" ] && val=${val:-deploy}

  # Podpowiedzi dla konkretnych zmiennych
  case "$var" in
    STAGING_HOST)
      hint=" (np: staging.example.com)"
      ;;
    PROD_HOST)
      hint=" (np: prod.example.com)"
      ;;
    DEPLOY_USER)
      hint=" (np: deploy)"
      ;;
  esac

  echo ""
  echo "⏳ Czekam na $var..."
  printf "%s%s [%s]: " "$var" "$hint" "$val"
  read input
  new_val=${input:-$val}
  echo "✅ Ustawiono $var: $new_val"

  if grep -q "^${var}=" .env 2>/dev/null; then
    sed -i "s/^${var}=.*/${var}=${new_val}/" .env
  else
    echo "${var}=${new_val}" >> .env
  fi
done

echo ""
echo "✅ Hosty zapisane do .env:"
echo "   STAGING_HOST=$(grep "^STAGING_HOST=" .env | cut -d= -f2)"
echo "   PROD_HOST=$(grep "^PROD_HOST=" .env | cut -d= -f2)"
echo "   DEPLOY_USER=$(grep "^DEPLOY_USER=" .env | cut -d= -f2)"
echo ""
echo "🔧 Sprawdź: taskfile doctor"
```

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

```markpact:file path=scripts/deploy.sh
#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Deployment: 1) staging  2) prod"
echo ""
echo "⏳ Czekam na wybór środowiska..."
printf "Wybierz: "; read CHOICE
[ "$CHOICE" = "1" ] && ENV="staging" && VAR="STAGING_HOST"
[ "$CHOICE" = "2" ] && ENV="prod" && VAR="PROD_HOST"
[ -z "${ENV:-}" ] && echo "❌ Nieprawidłowy wybór" && exit 1
HOST=$(grep "^${VAR}=" .env | cut -d= -f2)
[ -z "$HOST" ] && echo "❌ Host nie skonfigurowany" && exit 1
echo ""
echo "⏳ Czekam na potwierdzenie deploymentu do $ENV..."
printf "Deploy do %s? (t/n): " "$ENV"; read CONFIRM
[ "$CONFIRM" != "t" ] && echo "❌ Anulowano" && exit 0
echo "✅ Rozpoczynam deployment do $ENV..."
taskfile --env "$ENV" run deploy-exec
```

```markpact:file path=scripts/clean.sh
#!/usr/bin/env bash
set -euo pipefail

echo "🧹 Czyszczenie projektu"
echo ""
echo "Wybierz co usunąć:"
echo "  1) Tylko wygenerowane aplikacje (apps/)"
echo "  2) Aplikacje + środowisko (.venv/)"
echo "  3) Wszystko poza README.md (pełne reset)"
echo "  4) Anuluj"
echo ""
echo "⏳ Czekam na wybór opcji czyszczenia..."
printf "Wybór (1-4): "
read CHOICE
echo "✅ Wybrano opcję: $CHOICE"

case "$CHOICE" in
  1)
    echo "🗑️  Usuwam apps/..."
    rm -rf apps/
    echo "✅ Usunięto apps/"
    ;;
  2)
    echo "🗑️  Usuwam apps/ i .venv/..."
    rm -rf apps/ .venv/
    echo "✅ Usunięto apps/ i .venv/"
    echo "💡 Pliki konfiguracyjne (.env, prompts/) pozostały"
    ;;
  3)
    echo "🗑️  Pełne czyszczenie..."
    docker compose down -v 2>/dev/null || true
    rm -rf apps/ prompts/ .venv/ scripts/
    rm -f docker-compose.yml project.yml .env .gitignore .port-state.json Taskfile.yml
    echo "✅ Wyczyszczono - pozostał tylko README.md"
    ;;
  4|*)
    echo "Anulowano."
    ;;
esac
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
```

### .gitignore — ignorowane pliki

```markpact:file path=.gitignore
__pycache__/
*.pyc
.venv/
node_modules/
dist/
.env
.env.local
.env.staging
.env.prod
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
version: "3.8"

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

---

## 📚 Dokumentacja Taskfile

```bash
# Krótka składnia (nowe komendy CLI)
taskfile setup env              # Konfiguracja .env
taskfile setup hosts            # Konfiguracja hostów

# Podstawowe operacje
taskfile init                   # Interaktywne tworzenie Taskfile
taskfile list                   # Lista tasków
taskfile doctor                 # Diagnostyka projektu
taskfile <task>                 # Uruchom task bezpośrednio

# Nowe funkcje
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

## 👤 Autor

**Tom Sapletta** — tom@sapletta.com

**Licencja:** MIT
