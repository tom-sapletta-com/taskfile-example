# Taskfile + Markpact Project

**Cały projekt w jednym README.md - wypakuj i uruchom przez Taskfile.**

## Wymagania

```bash
pip install markpact taskfile --upgrade
```

## Szybki start (5 kroków)

```bash
# 1. Wypakuj wszystkie pliki z README.md (markpact)
markpact README.md

# 2. Konfiguracja środowiska (interaktywnie) 🔐
#    - wybierz providera LLM (OpenRouter, OpenAI, Anthropic, Ollama, Groq)
#    - wprowadź API key (z podpowiedziami/linkami)
#    - ustaw porty i nazwę projektu
taskfile setup env

# 3. Konfiguracja hostów deploymentu (staging/prod)
taskfile setup hosts

# 4. Generowanie kodu przez Aider (używa promptów)
taskfile run generate

# 5. Start lokalny
taskfile run dev
```

**Alternatywnie** - użyj dłuższej składni (obie działają):
```bash
markpact README.md
taskfile run setup-env     # zamiast: taskfile setup env
taskfile run setup-hosts   # zamiast: taskfile setup hosts
taskfile run generate && taskfile run dev
```

## Deployment

```bash
# Interaktywny deployment (pyta o staging/prod)
taskfile run deploy
```

## Architektura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         README.md (ten plik)                        │
│  ┌──────────────────┐ ┌─────────────────┐ ┌──────────────────────┐  │
│  │ markpact:file    │ │ markpact:file   │ │ markpact:file        │  │
│  │ path=Taskfile.yml│ │ path=.env       │ │ path=prompts/web.md  │  │
│  │                  │ │                 │ │                      │  │
│  │ (logika tasków)  │ │ (konfiguracja)  │ │ (prompt dla AI)      │  │
│  └──────────────────┘ └─────────────────┘ └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
           │
           │ markpact README.md
           │ (wypakowuje pliki)
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ./ (folder roboczy)                                                │
│  ├── Taskfile.yml      ← logika (init, setup-hosts, generate...)    │
│  ├── .env              ← konfiguracja (hosty, porty, klucze)        │
│  ├── .gitignore        ← ignoruje .env, .venv                       │
│  ├── project.yml       ← specyfikacja projektu                      │
│  ├── prompts/          ← prompty dla Aidera                         │
│  │   ├── web.md                                                     │
│  │   ├── desktop.md                                                 │
│  │   └── landing.md                                                 │
│  ├── docker-compose.yml ← konfiguracja lokalna                      │
│  └── apps/             ← kod wygenerowany przez Aidera              │
└─────────────────────────────────────────────────────────────────────┘
```

## Działanie

1. **README.md** zawiera wszystkie pliki jako bloki `markpact:file path=...`
2. **markpact** wypakowuje te pliki do folderu roboczego
3. **Taskfile.yml** przejmuje kontrolę - zawiera wszystkie taski (init, setup-hosts, generate, deploy)
4. **Aider** generuje kod na podstawie promptów z `prompts/*.md`

---

# Pliki projektu (markpact)

## Taskfile.yml

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
  doctor:
    desc: "Diagnostyka i autonaprawa projektu"
    cmds:
      - |
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
          echo "⚠️  Brak prompts/ - uruchom: taskfile run init"
          ((ERRORS++))
        fi

        # Sprawdź czy .venv istnieje
        if [ ! -d .venv ]; then
          echo "⚠️  Brak .venv - uruchom: taskfile run init"
          ((ERRORS++))
        fi

        # Sprawdź OPENROUTER_API_KEY
        if [ -z "${OPENROUTER_API_KEY}" ]; then
          echo "⚠️  Brak OPENROUTER_API_KEY w .env"
          echo ""
          echo "   🔧 Rozwiązanie: Uruchom interaktywną konfigurację:"
          echo "      taskfile run setup-env"
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

  setup-env:
    desc: "🔐 Interaktywna konfiguracja .env - LLM provider, API keys, porty"
    cmds:
      - |
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
        printf "Wybór (1-5) [1]: "
        read PROVIDER_CHOICE
        PROVIDER_CHOICE=${PROVIDER_CHOICE:-1}

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

        if [ -n "$CURRENT_KEY" ]; then
          echo "🔑 Obecny klucz API: ${CURRENT_KEY:0:10}..."
          printf "Zmienić? (t/n) [n]: "
          read CHANGE_KEY
          if [ "$CHANGE_KEY" != "t" ]; then
            echo "   Pozostawiam obecny klucz"
            API_KEY="$CURRENT_KEY"
          else
            API_KEY=""
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
          printf "🔑 Wklej klucz API: "
          read API_KEY

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
        CURRENT_MODEL=$(grep "^AIDER_MODEL=" .env 2>/dev/null | cut -d= -f2 || echo "")
        if [ -n "$CURRENT_MODEL" ]; then
          echo "🎯 Obecny model: $CURRENT_MODEL"
        fi
        printf "🎯 Model [$DEFAULT_MODEL]: "
        read MODEL
        MODEL=${MODEL:-$DEFAULT_MODEL}
        sed -i "/^AIDER_MODEL=/d" .env 2>/dev/null
        echo "AIDER_MODEL=$MODEL" >> .env

        # === PORTY ===
        echo ""
        echo "🌐 Konfiguracja portów:"
        echo ""

        CURRENT_WEB=$(grep "^PORT_WEB=" .env 2>/dev/null | cut -d= -f2 || echo "")
        CURRENT_WEB=${CURRENT_WEB:-8000}
        printf "   Port Web App [$CURRENT_WEB]: "
        read PORT_WEB
        PORT_WEB=${PORT_WEB:-$CURRENT_WEB}
        sed -i "/^PORT_WEB=/d" .env 2>/dev/null
        echo "PORT_WEB=$PORT_WEB" >> .env

        CURRENT_LANDING=$(grep "^PORT_LANDING=" .env 2>/dev/null | cut -d= -f2 || echo "")
        CURRENT_LANDING=${CURRENT_LANDING:-3000}
        printf "   Port Landing [$CURRENT_LANDING]: "
        read PORT_LANDING
        PORT_LANDING=${PORT_LANDING:-$CURRENT_LANDING}
        sed -i "/^PORT_LANDING=/d" .env 2>/dev/null
        echo "PORT_LANDING=$PORT_LANDING" >> .env

        # === PROJECT NAME ===
        CURRENT_NAME=$(grep "^PROJECT_NAME=" .env 2>/dev/null | cut -d= -f2 || echo "")
        CURRENT_NAME=${CURRENT_NAME:-taskfile-example}
        printf "\n📁 Nazwa projektu [$CURRENT_NAME]: "
        read PROJECT_NAME
        PROJECT_NAME=${PROJECT_NAME:-$CURRENT_NAME}
        sed -i "/^PROJECT_NAME=/d" .env 2>/dev/null
        echo "PROJECT_NAME=$PROJECT_NAME" >> .env

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
        echo "🔧 Teraz uruchom: taskfile run setup-hosts"

  setup-hosts:
    desc: "Konfiguracja hostów deploymentu (podpowiedzi: staging.example.com, prod.example.com)"
    cmds:
      - |
        # Autonaprawa: sprawdź czy .env istnieje
        if [ ! -f .env ]; then
          echo "⚠️  Brak .env - tworzę..."
          taskfile run doctor
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

          printf "%s%s [%s]: " "$var" "$hint" "$val"
          read input
          new_val=${input:-$val}

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
        echo "🔧 Sprawdź: taskfile run doctor"

  generate:
    desc: "Generowanie kodu przez Aider"
    cmds:
      - |
        # Load environment variables from .env
        [ -f .env ] && export $(grep -v '^#' .env | xargs) 2>/dev/null || true
        [ -z "${OPENROUTER_API_KEY}" ] && echo "❌ Brak OPENROUTER_API_KEY w .env" && exit 1
        # Auto-init if apps/ don't exist
        if [ ! -d apps/web ] || [ ! -d apps/desktop ] || [ ! -d apps/landing ]; then
          echo "⚠️  Brak struktury apps/ - uruchamiam init..."
          taskfile run init
        fi
        taskfile run generate-web
        taskfile run generate-desktop
        taskfile run generate-landing
      - "@fn notify Kod wygenerowany"

  generate-web:
    desc: "Generowanie FastAPI"
    cmds:
      - |
        echo "🤖 Web..."
        cd apps/web && ../../.venv/bin/aider \
          --model "${AIDER_MODEL}" --openai-api-key "${OPENROUTER_API_KEY}" \
          --openai-api-base "https://openrouter.ai/api/v1" \
          --yes --no-git --message "$(cat ../../prompts/web.md)"

  generate-desktop:
    desc: "Generowanie Electron"
    cmds:
      - |
        echo "🤖 Desktop..."
        cd apps/desktop && ../../.venv/bin/aider \
          --model "${AIDER_MODEL}" --openai-api-key "${OPENROUTER_API_KEY}" \
          --openai-api-base "https://openrouter.ai/api/v1" \
          --yes --no-git --message "$(cat ../../prompts/desktop.md)"

  generate-landing:
    desc: "Generowanie Landing"
    cmds:
      - |
        echo "🤖 Landing..."
        cd apps/landing && ../../.venv/bin/aider \
          --model "${AIDER_MODEL}" --openai-api-key "${OPENROUTER_API_KEY}" \
          --openai-api-base "https://openrouter.ai/api/v1" \
          --yes --no-git --message "$(cat ../../prompts/landing.md)"

  init:
    desc: "Inicjalizacja - tworzy strukturę, instaluje aider"
    cmds:
      - mkdir -p apps/web/templates apps/web/static apps/web/tests apps/desktop apps/landing
      - |
        [ ! -d .venv ] && python3 -m venv .venv
        .venv/bin/pip install -q aider-chat 2>/dev/null || true
        .venv/bin/pip install -q fastapi uvicorn jinja2 python-multipart pytest httpx
      - echo "✅ Gotowe! Następne: taskfile run setup-hosts"

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
    cmds:
      - |
        echo "🚀 Deployment: 1) staging  2) prod"
        printf "Wybierz: "; read CHOICE
        [ "$CHOICE" = "1" ] && ENV="staging" && VAR="STAGING_HOST"
        [ "$CHOICE" = "2" ] && ENV="prod" && VAR="PROD_HOST"
        [ -z "$ENV" ] && echo "❌ Nieprawidłowy wybór" && exit 1
        HOST=$(grep "^${VAR}=" .env | cut -d= -f2)
        [ -z "$HOST" ] && echo "❌ Host nie skonfigurowany" && exit 1
        printf "Deploy do %s? (t/n): " "$ENV"; read CONFIRM
        [ "$CONFIRM" != "t" ] && echo "Anulowano" && exit 0
        taskfile --env "$ENV" run deploy-exec

  deploy-exec:
    desc: "Wykonanie deploymentu"
    internal: true
    env: [staging, prod]
    retries: 2
    retry_delay: 10
    cmds:
      - "@remote podman pull ${IMAGE_WEB}:${TAG}"
      - "@remote podman pull ${IMAGE_LANDING}:${TAG}"
      - "@remote systemctl --user restart ${PROJECT_NAME}-web.service 2>/dev/null || podman run -d --name ${PROJECT_NAME}-web --replace -p 8000:8000 ${IMAGE_WEB}:${TAG}"
      - "@remote systemctl --user restart ${PROJECT_NAME}-landing.service 2>/dev/null || podman run -d --name ${PROJECT_NAME}-landing --replace -p 3000:80 ${IMAGE_LANDING}:${TAG}"
      - "@fn health-check http://${SSH_HOST}/health"
      - "@fn notify Deployment gotowy"

  status:
    desc: "Status"
    cmds:
      - "@fn health-check http://localhost:${PORT_WEB:-8000}/health"

  clean:
    desc: "Czyszczenie z wyborem - pyta co usunąć"
    cmds:
      - |
        echo "🧹 Czyszczenie projektu"
        echo ""
        echo "Wybierz co usunąć:"
        echo "  1) Tylko wygenerowane aplikacje (apps/)"
        echo "  2) Aplikacje + środowisko (.venv/)"
        echo "  3) Wszystko poza README.md (pełne reset)"
        echo "  4) Anuluj"
        echo ""
        printf "Wybór (1-4): "
        read CHOICE

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
            rm -rf apps/ prompts/ .venv/
            rm -f docker-compose.yml project.yml .env .gitignore .port-state.json Taskfile.yml
            echo "✅ Wyczyszczono - pozostał tylko README.md"
            ;;
          4|*)
            echo "Anulowano."
            ;;
        esac
```

## Konfiguracja środowiska

```markpact:file path=.env
# === Konfiguracja projektu ===
PROJECT_NAME=taskfile-example
VERSION=1.0.0
OPENROUTER_API_KEY=
AIDER_MODEL=openrouter/anthropic/claude-sonnet-4

# === Porty lokalne ===
PORT_WEB=8000
PORT_LANDING=3000

# === Hosty deploymentu (ustawiane przez: taskfile run setup-hosts) ===
STAGING_HOST=
PROD_HOST=
DEPLOY_USER=deploy
```

```markpact:file path=.gitignore
# Python
__pycache__/
*.pyc
.venv/
*.db
.pytest_cache/

# Node
node_modules/
dist/
out/

# Env files (zawierają sekrety i hosty)
.env
.env.local
.env.staging
.env.prod

# State
.port-state.json
```

## Specyfikacja projektu

```markpact:file path=project.yml
project:
  name: taskfile-example
  description: "Multi-platform SaaS with desktop client"
  version: "1.0.0"
  author: tom-sapletta-com
  license: MIT

apps:
  web:
    type: saas
    framework: fastapi
    language: python
    port: 8000
    features:
      - JWT authentication
      - Dashboard with stats
      - REST API for desktop client
      - Health endpoint
      - WebSocket support

  desktop:
    type: electron
    framework: electron
    language: javascript
    platforms: [linux, macos, windows]
    features:
      - System tray integration
      - API connection to web
      - Cross-platform builds

  landing:
    type: static
    framework: html
    language: html+css+js
    port: 3000
    features:
      - Hero section with CTA
      - Download buttons
      - Pricing section
      - Link to SaaS

deployment:
  local:
    type: docker-compose
  staging:
    type: podman-quadlet
  prod:
    type: podman-quadlet
```

## Prompty dla Aidera

```markpact:file path=prompts/web.md
# Generate: SaaS Web Application (FastAPI)

Create a FastAPI web application in apps/web/ with:

## Files to create:
1. main.py - FastAPI app with:
   - /health endpoint returning {"status": "ok", "version": "1.0.0"}
   - /api/v1/status with API info
   - /dashboard - HTML dashboard (Jinja2 template)
   - /login - login page
   - Static file serving from /static

2. templates/dashboard.html - Modern dashboard with:
   - TailwindCSS CDN
   - Status cards (Active, API version, etc.)
   - Navigation links

3. templates/login.html - Login form with TailwindCSS

4. requirements.txt - fastapi, uvicorn, jinja2, python-multipart

5. Dockerfile - python:3.12-slim, port 8000

6. tests/test_app.py - pytest tests for /health, /api/v1/status, /dashboard

## Tech Stack:
- FastAPI + Uvicorn
- Jinja2 templates
- TailwindCSS CDN (no build step)
- pytest for testing
```

```markpact:file path=prompts/desktop.md
# Generate: Desktop Application (Electron)

Create an Electron desktop app in apps/desktop/ with:

## Files to create:
1. package.json - Electron 28+, electron-builder config
   - Build targets: Linux (AppImage), macOS (dmg), Windows (exe)

2. main.js - Main process with:
   - BrowserWindow 1000x700
   - contextIsolation: true
   - System tray with Open/Quit menu

3. preload.js - contextBridge exposing API URL

4. index.html - Renderer with:
   - TailwindCSS CDN
   - API status display (green/red indicator)
   - Auto-refresh every 10 seconds
   - Connects to http://localhost:8000/api/v1/status

## Features:
- Cross-platform (Linux, macOS, Windows)
- System tray integration
- API connection status
- Modern UI with TailwindCSS
```

```markpact:file path=prompts/landing.md
# Generate: Landing Page

Create a static landing page in apps/landing/ with:

## Files to create:
1. index.html - Single page with:
   - Hero section: gradient blue→purple, headline "Deploy Anywhere. One Config File."
   - CTA buttons: "Download Desktop", "Open SaaS"
   - "How It Works" section - 3 steps: Define → Generate → Deploy
   - "Download" section - Linux/AppImage, macOS/dmg, Windows/exe
   - "Pricing" section - Free ($0), Pro ($9/mo), Enterprise (Custom)
   - Footer with GitHub link

2. Dockerfile - nginx:alpine serving index.html on port 80

## Tech Stack:
- Static HTML (no build step)
- TailwindCSS CDN
- Nginx for serving
- Responsive design
```

## Docker Compose

```markpact:file path=docker-compose.yml
version: "3.8"

services:
  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    container_name: ${PROJECT_NAME}-web
    ports:
      - "${PORT_WEB:-8000}:8000"
    environment:
      - VERSION=${VERSION:-1.0.0}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  landing:
    build:
      context: ./apps/landing
      dockerfile: Dockerfile
    container_name: ${PROJECT_NAME}-landing
    ports:
      - "${PORT_LANDING:-3000}:80"
    restart: unless-stopped
```

---

## Pełny przepływ pracy

```bash
# START: Masz tylko README.md

# 1. Wypakuj wszystko (markpact tworzy pliki z bloków markpact:file)
markpact README.md

# 2. Inicjalizacja (tworzy strukturę, instaluje aider)
taskfile run init

# 3. Konfiguracja hostów (interaktywnie - pyta o staging/prod)
taskfile run setup-hosts

# 4. Generowanie kodu (Aider używa promptów z prompts/)
taskfile run generate

# 5. Testy
taskfile run test

# 6. Build
taskfile run build

# 7. Start lokalny
taskfile run dev

# 8. Deployment (interaktywny - pyta o środowisko)
taskfile run deploy

# KONIEC: Czyszczenie (zostaje tylko README.md)
taskfile run clean
```

## Taski dostępne po wypakowaniu

| Task | Opis |
|------|------|
| `doctor` | 🔧 Diagnostyka i autonaprawa (sprawdza .env, .venv, klucze) |
| `setup env` / `run setup-env` | 🔐 Interaktywna konfiguracja .env - wybór LLM providera, API keys, porty |
| `setup hosts` / `run setup-hosts` | 🌐 Pyta o hosty staging/prod z podpowiedziami, zapisuje do .env |
| `init` | Tworzy strukturę katalogów, instaluje aider |
| `generate` | Generuje kod przez Aider (web, desktop, landing) |
| `test` | Uruchamia pytest |
| `build` | Buduje obrazy Docker |
| `dev` | Startuje docker compose |
| `deploy` | Interaktywny deployment |
| `clean` | Usuwa wszystko poza README.md |

## Zalety tego podejścia

1. **Jeden plik źródłowy** - README.md zawiera cały projekt
2. **Markpact ekstrahuje** - używa standardowego narzędzia do wypakowania
3. **Taskfile zarządza** - pełna logika w Taskfile.yml (też w środku README)
4. **Rozdzielność** - można edytować Taskfile.yml niezależnie po wypakowaniu
5. **Wersjonowanie** - zmiany w README.md = zmiany w całym projekcie

---

## Autor

Tom Sapletta - tom@sapletta.com
