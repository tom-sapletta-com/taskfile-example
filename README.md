# taskfile-example

**Multi-platform deployment with AI code generation — all from one `Taskfile.yml`.**

One YAML file defines your entire project: SaaS web app, desktop client, landing page.
An LLM agent generates the code, Taskfile deploys it everywhere.

```
┌─────────────────────────────────────────────────────────────┐
│                      Taskfile.yml                           │
│         (project contract = single source of truth)         │
│                                                             │
│  ┌───────────┐   ┌──────────┐   ┌──────────┐                │
│  │  Web App  │   │ Desktop  │   │ Landing  │  ← apps        │
│  │ (FastAPI) │   │(Electron)│   │  (HTML)  │                │
│  └────┬──────┘   └────┬─────┘   └────┬─────┘                │
│       │               │              │                      │
│  ┌────┴───────────────┴──────────────┴───┐                  │
│  │     LLM Agent (opencode/goose/aider)  │  ← generates     │
│  └────┬──────────────┬──────────────┬────┘                  │
│       │              │              │                       │
│  ┌────┴─────┐   ┌────┴─────┐   ┌────┴─────┐                 │
│  │  Docker  │   │ Electron │   │  Nginx   │  ← packages     │
│  │ :8000    │   │ AppImage │   │  :3000   │                 │
│  └────┬─────┘   └──────────┘   └────┬─────┘                 │
│       │                             │                       │
│  ┌────┴─────────────────────────────┴────┐                  │
│  │  local (compose) │ staging │ prod     │  ← deploys       │
│  │  Docker Compose  │ Podman  │ Quadlet  │                  │
│  └───────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Generate all app code (no API key needed — uses built-in templates)
taskfile run generate-all

# 2. Start everything locally
taskfile run dev

# 3. Open in browser
#    🌐 Web app   → http://localhost:8000
#    🖥️  Landing   → http://localhost:3000
```

### With LLM Agent (AI-generated code)

```bash
# Set your OpenRouter API key
export OPENROUTER_API_KEY=sk-or-...

# Choose your agent
export LLM_AGENT=opencode   # or: goose, aider

# Generate with AI
taskfile run generate-all

# Full pipeline: generate → test → build → deploy
taskfile run release
```

---

## Project Structure

```
taskfile-example/
├── Taskfile.yml              # Master config — 26 tasks, 3 envs, 4 functions
├── project.yml               # Project spec (what to build)
├── docker-compose.yml        # Local development
├── .env.local                # Local env vars
│
├── .agent/
│   └── prompts/              # LLM prompts per app
│       ├── web.md
│       ├── desktop.md
│       └── landing.md
│
├── apps/
│   ├── web/                  # FastAPI SaaS app
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── templates/
│   │   └── tests/
│   ├── desktop/              # Electron desktop app
│   │   ├── main.js
│   │   ├── package.json
│   │   └── index.html
│   └── landing/              # Static landing page
│       ├── index.html
│       └── Dockerfile
│
├── scripts/
│   ├── agent.py              # LLM agent dispatcher
│   └── monitor.py            # Health monitoring
│
└── deploy/                   # Deployment configs (per-environment)
```

---

## How It Works

### 1. Project Contract (`Taskfile.yml` + `project.yml`)

`project.yml` describes **what** to build (apps, features, deployment targets).
`Taskfile.yml` describes **how** to build, test, deploy, and monitor.

### 2. Code Generation (`@fn llm-generate`)

The `functions` section in Taskfile.yml defines an LLM agent dispatcher:

```yaml
functions:
  llm-generate:
    lang: python
    file: scripts/agent.py
```

Tasks call it with `@fn llm-generate <target>`:

```yaml
tasks:
  generate-web:
    cmds:
      - "@fn llm-generate web"
```

The agent reads the prompt from `.agent/prompts/web.md` and dispatches to the configured LLM:

| Agent | Command | Backend |
|-------|---------|---------|
| **opencode** | `opencode --dir apps/web --message "..."` | OpenRouter (native) |
| **goose** | `goose run --dir apps/web --file prompt.md` | OpenRouter / Ollama |
| **aider** | `aider --model ... --yes --message "..."` | OpenRouter / OpenAI |
| **direct** | built-in templates (no API key) | None — scaffold only |

### 3. Multi-Platform Deployment

```bash
# Local — Docker Compose
taskfile --env local run dev

# Staging — Podman over SSH
taskfile --env staging run deploy-all

# Production — Podman Quadlet over SSH
taskfile --env prod run deploy-all

# All remotes at once — rolling strategy
taskfile -G all-remote run deploy-all
```

### 4. Monitoring

```bash
# Check health of all services
taskfile run status

# Full monitoring suite
taskfile run monitor

# View logs
taskfile --env prod run logs-web
taskfile --env prod run logs-landing
```

---

## All Tasks (26)

| Task | Description | Tags |
|------|-------------|------|
| `init` | Initialize project, install deps | — |
| **Generate** | | |
| `generate-web` | Generate SaaS web app via LLM | generate, web |
| `generate-desktop` | Generate desktop app via LLM | generate, desktop |
| `generate-landing` | Generate landing page via LLM | generate, landing |
| `generate-all` | Generate ALL apps (parallel) | generate |
| **Test** | | |
| `test-web` | Test web app (pytest) | test, web, ci |
| `test-desktop` | Test desktop app (npm test) | test, desktop, ci |
| `test-landing` | Validate landing page | test, landing, ci |
| `test-all` | Run all tests (parallel) | test, ci |
| **Build** | | |
| `build-web` | Build web Docker image | build, web, ci |
| `build-desktop` | Build Electron packages | build, desktop |
| `build-landing` | Build landing Docker image | build, landing, ci |
| `build-all` | Build all (parallel) | build, ci |
| **Deploy** | | |
| `deploy-web` | Deploy web to staging/prod | deploy, web |
| `deploy-landing` | Deploy landing to staging/prod | deploy, landing |
| `deploy-all` | Deploy everything | deploy |
| **Dev** | | |
| `dev` | Start all locally (compose) | dev |
| `dev-web` | Start web with hot reload | dev, web |
| `dev-landing` | Start landing locally | dev, landing |
| **Monitor** | | |
| `status` | Health check all services | monitoring |
| `monitor` | Full monitoring suite | monitoring |
| `logs-web` | View web app logs (remote) | monitoring, web |
| `logs-landing` | View landing logs (remote) | monitoring, landing |
| **Release** | | |
| `release` | Full pipeline → staging | release |
| `release-prod` | Promote to production | release |
| `clean` | Remove artifacts | — |

### Tag-Based Execution

```bash
# Run only CI tasks
taskfile run test-all build-all --tags ci

# Run only deploy tasks
taskfile run deploy-web deploy-landing --tags deploy

# Run only web-related tasks
taskfile run generate-web test-web build-web --tags web
```

---

## LLM Agent Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_AGENT` | `direct` | Agent: `opencode`, `goose`, `aider`, `direct` |
| `LLM_MODEL` | `openrouter/anthropic/claude-sonnet-4` | Model for OpenRouter |
| `OPENROUTER_API_KEY` | — | API key (required for LLM agents) |

### Installing Agents

```bash
# opencode — fully open-source, native OpenRouter support
pip install opencode

# Goose CLI — open-source terminal agent
pip install goose-ai

# Aider — open-source pair programmer
pip install aider-chat
```

---

## Environments

| Environment | Runtime | Manager | Access |
|-------------|---------|---------|--------|
| `local` | Docker | Compose | `localhost` |
| `staging` | Podman | Quadlet | SSH `staging.example.com` |
| `prod` | Podman | Quadlet | SSH `prod.example.com` |

### Environment Group

```yaml
environment_groups:
  all-remote:
    members: [staging, prod]
    strategy: rolling
    max_parallel: 1
```

---

## Ansible-Inspired Features

Tasks support retry, timeout, tags, and output capture:

```yaml
deploy-web:
  retries: 2          # retry on failure
  retry_delay: 10     # 10s between retries
  timeout: 300        # abort after 5 minutes
  tags: [deploy, web] # filter with --tags
  register: OUTPUT    # capture stdout
```

---

## Embedded Functions

4 functions defined in Taskfile.yml:

| Function | Lang | Description |
|----------|------|-------------|
| `llm-generate` | Python (file) | Dispatch code generation to LLM agent |
| `health-check` | Shell (inline) | HTTP health check with 10 retries |
| `notify` | Python (inline) | Slack/stdout notification |
| `monitor` | Python (file) | Full monitoring suite |

---

## CI/CD Pipeline

5 stages defined in the `pipeline` section → auto-generates configs for GitHub Actions, GitLab CI, etc:

```bash
taskfile ci generate --target github
taskfile ci generate --target gitlab
```

---

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Author

Created by **Tom Sapletta** - [tom@sapletta.com](mailto:tom@sapletta.com)
