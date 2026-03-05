# 1/ — One-File Bootstrap

**Start with ONLY `Taskfile.yml`. One command generates, builds, and deploys everything.**

```
BEFORE (1 file):                    AFTER (auto-generated):
┌──────────────┐                    ┌──────────────────────────┐
│ Taskfile.yml │  ──bootstrap──►    │ Taskfile.yml             │
└──────────────┘                    │ .venv/ (aider + deps)    │
                                    │ .env                     │
                                    │ docker-compose.yml       │
                                    │ .gitignore               │
                                    │ apps/                    │
                                    │   web/      (FastAPI)    │
                                    │   desktop/  (Electron)   │
                                    │   landing/  (HTML+Nginx) │
                                    └──────────────────────────┘
```

---

## Quick Start (2 commands)

```bash
pip install taskfile
taskfile run bootstrap
```

That's it. After `bootstrap`:
- **http://localhost:8000** — SaaS web app (FastAPI + TailwindCSS)
- **http://localhost:3000** — Landing page with downloads + pricing
- **http://localhost:8000/dashboard** — Dashboard
- `.venv/` contains aider-chat, ready for AI-powered regeneration

---

## How It Works

### Without API key (default — inline templates)

```bash
taskfile run bootstrap
```

The Taskfile contains inline code templates as heredocs. When `OPENROUTER_API_KEY` is empty, it generates working apps from these built-in templates. **No LLM needed.**

### With API key (Aider generates real code)

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
taskfile run bootstrap
```

Now Aider is called for each app with a detailed prompt. Aider uses Claude via OpenRouter to generate production-quality code.

---

## Step by Step

| Step | Command | What happens |
|------|---------|--------------|
| 1 | `taskfile run setup` | Creates `.venv/`, installs `aider-chat` + FastAPI deps, creates `.env` |
| 2 | `taskfile run generate` | Runs Aider (or inline templates) for web, desktop, landing |
| 3 | `taskfile run test` | Runs pytest on web app |
| 4 | `taskfile run dev` | `docker compose up` — all apps running |
| 5 | `taskfile run release` | test → build → deploy to staging |
| 6 | `taskfile run release-prod` | Deploy to production |
| **all** | `taskfile run bootstrap` | Steps 1+2+4 in one command |

---

## What's Inside the Taskfile

### Configuration (top of file)

```yaml
variables:
  AIDER_MODEL: openrouter/anthropic/claude-sonnet-4   # which model
  OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:-}          # your API key
  IMAGE_WEB: ghcr.io/tom-sapletta-com/...-web          # Docker image names
```

### Auto-install of Aider (`setup` task)

```yaml
setup:
  cmds:
    - python3 -m venv .venv
    - .venv/bin/pip install -q aider-chat       # ← auto-installed
    - .venv/bin/pip install -q fastapi uvicorn pytest
    - mkdir -p apps/web apps/desktop apps/landing
```

### Code Generation (`generate-web` task)

Two paths:
1. **No API key** → inline heredoc templates (works offline)
2. **With API key** → Aider with detailed prompt:

```yaml
generate-web:
  cmds:
    - |
      if [ -z "${OPENROUTER_API_KEY}" ]; then
        # inline template (cat > main.py << 'EOF' ...)
      else
        .venv/bin/aider \
          --model "${AIDER_MODEL}" \
          --openai-api-key "${OPENROUTER_API_KEY}" \
          --openai-api-base "https://openrouter.ai/api/v1" \
          --yes --no-git \
          --message "Create a FastAPI SaaS web app..."
      fi
```

### Deployment (`deploy` task)

```yaml
deploy:
  env: [staging, prod]
  retries: 2
  retry_delay: 10
  timeout: 300
  cmds:
    - "@remote podman pull ${IMAGE_WEB}:${TAG}"
    - "@remote podman run -d ... ${IMAGE_WEB}:${TAG}"
    - "@fn health-check http://${DOMAIN_WEB}/health"
```

---

## All 16 Tasks

| Task | Description |
|------|-------------|
| `bootstrap` | **ONE COMMAND** — setup + generate + dev |
| `setup` | Install aider + create venv + skeleton |
| `generate` | Generate all 3 apps |
| `generate-web` | Aider → FastAPI SaaS |
| `generate-desktop` | Aider → Electron app |
| `generate-landing` | Aider → Landing page |
| `generate-infra` | Create docker-compose.yml + .gitignore |
| `test` | Run pytest |
| `build` | Build Docker images |
| `dev` | docker compose up (local) |
| `dev-web` | uvicorn with hot reload |
| `deploy` | Deploy to staging/prod via SSH |
| `release` | test → build → deploy staging |
| `release-prod` | Deploy to production |
| `status` | Health check all services |
| `clean` | Remove everything → back to 1 file |

---

## Cleanup (back to 1 file)

```bash
taskfile run clean
```

Removes all generated code, containers, images. Only `Taskfile.yml` remains.

---

## vs. Root Example

| | `1/` (this) | Root (`../`) |
|---|---|---|
| Starting files | **1** (Taskfile.yml) | 15+ files |
| Agent install | Auto (`setup` task) | Manual |
| Code templates | Inline heredocs | Separate Python script |
| Agents supported | Aider | opencode, Goose, Aider |
| Prompts | Inline in tasks | `.agent/prompts/*.md` |
| Functions | 2 (inline) | 4 (inline + file) |
| Best for | Quick start, demos | Production, extensible |
