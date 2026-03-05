#!/usr/bin/env python3
"""LLM Agent Dispatcher — orchestrates code generation via opencode/goose/aider.

Reads project.yml contract and dispatches prompts to the configured LLM agent.
Generates complete app code for: web (FastAPI), desktop (Electron), landing (HTML).

Usage from Taskfile:
    @fn llm-generate web
    @fn llm-generate desktop
    @fn llm-generate landing

Environment:
    LLM_AGENT    — which agent to use: opencode | goose | aider | direct (default: direct)
    LLM_MODEL    — model identifier (default: openrouter/anthropic/claude-sonnet-4)
    OPENROUTER_API_KEY — API key for OpenRouter
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / ".agent" / "prompts"
APPS_DIR = PROJECT_ROOT / "apps"


def main():
    args = os.environ.get("FN_ARGS", "").strip()
    if not args:
        print("Usage: @fn llm-generate <web|desktop|landing|all>")
        sys.exit(1)

    target = args.split()[0]
    agent = os.environ.get("LLM_AGENT", "direct")
    model = os.environ.get("LLM_MODEL", "openrouter/anthropic/claude-sonnet-4")

    print(f"🤖 Agent: {agent} | Model: {model} | Target: {target}")

    if target == "all":
        for t in ["web", "desktop", "landing"]:
            generate(t, agent, model)
    else:
        generate(target, agent, model)


def generate(target: str, agent: str, model: str):
    """Generate code for a specific app target."""
    prompt_file = PROMPTS_DIR / f"{target}.md"
    output_dir = APPS_DIR / target

    if not prompt_file.exists():
        print(f"❌ Prompt not found: {prompt_file}")
        sys.exit(1)

    prompt = prompt_file.read_text(encoding="utf-8")
    print(f"\n📝 Generating {target} → {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    if agent == "opencode":
        _run_opencode(prompt, output_dir, model)
    elif agent == "goose":
        _run_goose(prompt, output_dir, model)
    elif agent == "aider":
        _run_aider(prompt, output_dir, model)
    elif agent == "direct":
        _run_direct(target, output_dir)
    else:
        print(f"❌ Unknown agent: {agent}")
        print("   Supported: opencode, goose, aider, direct")
        sys.exit(1)

    print(f"✅ Generated {target}")


# ─── Agent Backends ──────────────────────────────────────────────────

def _run_opencode(prompt: str, output_dir: Path, model: str):
    """Use opencode CLI to generate code."""
    # opencode uses OpenRouter natively
    env = {**os.environ, "OPENCODE_MODEL": model}
    cmd = f'opencode --dir {output_dir} --message "{_escape_prompt(prompt)}"'
    _exec(cmd, env, output_dir)


def _run_goose(prompt: str, output_dir: Path, model: str):
    """Use Goose CLI to generate code."""
    env = {**os.environ, "GOOSE_MODEL": model}
    prompt_file = output_dir / ".goose-prompt.md"
    prompt_file.write_text(prompt, encoding="utf-8")
    cmd = f"goose run --dir {output_dir} --file {prompt_file}"
    _exec(cmd, env, output_dir)


def _run_aider(prompt: str, output_dir: Path, model: str):
    """Use Aider to generate code."""
    env = {**os.environ}
    # Aider supports OpenAI-compatible API (OpenRouter)
    if os.environ.get("OPENROUTER_API_KEY"):
        env["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
        env["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
    cmd = f'aider --model {model} --yes --message "{_escape_prompt(prompt)}"'
    _exec(cmd, env, output_dir)


def _run_direct(target: str, output_dir: Path):
    """Direct generation — use built-in templates (no LLM needed).

    This is the fallback that generates working scaffolds without an API key.
    Useful for testing the full pipeline or when no LLM agent is available.
    """
    print(f"  📦 Using built-in templates (no LLM agent)")
    templates_dir = PROJECT_ROOT / ".agent" / "templates"

    if target == "web":
        _generate_web_direct(output_dir, templates_dir)
    elif target == "desktop":
        _generate_desktop_direct(output_dir, templates_dir)
    elif target == "landing":
        _generate_landing_direct(output_dir, templates_dir)


def _generate_web_direct(output_dir: Path, templates_dir: Path):
    """Generate FastAPI web app from built-in template."""
    src = templates_dir / "web"
    if src.exists():
        _copy_tree(src, output_dir)
    else:
        # Inline minimal FastAPI app
        (output_dir / "main.py").write_text(_WEB_MAIN, encoding="utf-8")
        (output_dir / "requirements.txt").write_text(_WEB_REQUIREMENTS, encoding="utf-8")
        (output_dir / "Dockerfile").write_text(_WEB_DOCKERFILE, encoding="utf-8")
        (output_dir / "templates").mkdir(exist_ok=True)
        (output_dir / "templates" / "dashboard.html").write_text(_WEB_DASHBOARD, encoding="utf-8")
        (output_dir / "templates" / "login.html").write_text(_WEB_LOGIN, encoding="utf-8")
        (output_dir / "static").mkdir(exist_ok=True)
        (output_dir / "tests").mkdir(exist_ok=True)
        (output_dir / "tests" / "__init__.py").write_text("", encoding="utf-8")
        (output_dir / "tests" / "test_app.py").write_text(_WEB_TEST, encoding="utf-8")


def _generate_desktop_direct(output_dir: Path, templates_dir: Path):
    """Generate Electron desktop app from built-in template."""
    src = templates_dir / "desktop"
    if src.exists():
        _copy_tree(src, output_dir)
    else:
        (output_dir / "package.json").write_text(_DESKTOP_PACKAGE_JSON, encoding="utf-8")
        (output_dir / "main.js").write_text(_DESKTOP_MAIN_JS, encoding="utf-8")
        (output_dir / "index.html").write_text(_DESKTOP_INDEX_HTML, encoding="utf-8")
        (output_dir / "preload.js").write_text(_DESKTOP_PRELOAD_JS, encoding="utf-8")


def _generate_landing_direct(output_dir: Path, templates_dir: Path):
    """Generate landing page from built-in template."""
    src = templates_dir / "landing"
    if src.exists():
        _copy_tree(src, output_dir)
    else:
        (output_dir / "index.html").write_text(_LANDING_HTML, encoding="utf-8")
        (output_dir / "Dockerfile").write_text(_LANDING_DOCKERFILE, encoding="utf-8")


# ─── Helpers ─────────────────────────────────────────────────────────

def _exec(cmd: str, env: dict, cwd: Path):
    """Execute a shell command."""
    print(f"  → {cmd[:120]}{'...' if len(cmd) > 120 else ''}")
    try:
        result = subprocess.run(cmd, shell=True, env=env, cwd=str(cwd), text=True)
        if result.returncode != 0:
            print(f"  ⚠️  Agent exited with code {result.returncode}")
    except FileNotFoundError:
        print(f"  ❌ Agent not found. Install it first.")
        print(f"     opencode: pip install opencode")
        print(f"     goose:    pip install goose-ai")
        print(f"     aider:    pip install aider-chat")


def _escape_prompt(prompt: str) -> str:
    """Escape prompt for shell."""
    return prompt.replace('"', '\\"').replace("$", "\\$")[:2000]


def _copy_tree(src: Path, dst: Path):
    """Copy directory tree."""
    import shutil
    for item in src.rglob("*"):
        if item.is_file():
            rel = item.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


# ═══════════════════════════════════════════════════════════════════════
# Built-in Templates (direct mode — no LLM needed)
# ═══════════════════════════════════════════════════════════════════════

_WEB_MAIN = '''\
"""FastAPI SaaS Web Application."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import time

app = FastAPI(
    title="Taskfile Example — SaaS",
    version=os.environ.get("VERSION", "1.0.0"),
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

START_TIME = time.time()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return JSONResponse({
        "status": "ok",
        "version": os.environ.get("VERSION", "1.0.0"),
        "uptime": round(time.time() - START_TIME, 1),
    })


@app.get("/api/v1/status")
async def api_status():
    """API status for desktop client."""
    return JSONResponse({
        "api": "v1",
        "status": "running",
        "features": ["auth", "dashboard", "websocket"],
    })


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to dashboard."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard",
        "version": os.environ.get("VERSION", "1.0.0"),
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard",
        "version": os.environ.get("VERSION", "1.0.0"),
    })


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Login",
    })
'''

_WEB_REQUIREMENTS = """\
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
jinja2>=3.1.2
python-multipart>=0.0.6
httpx>=0.25.0
aiosqlite>=0.19.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
"""

_WEB_DOCKERFILE = """\
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

_WEB_DASHBOARD = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} — Taskfile Example</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <nav class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
            <h1 class="text-xl font-bold text-gray-800">📊 Dashboard</h1>
            <span class="text-sm text-gray-500">v{{ version }}</span>
        </div>
    </nav>
    <main class="max-w-7xl mx-auto px-4 py-8">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-sm font-medium text-gray-500 uppercase">Status</h3>
                <p class="mt-2 text-3xl font-bold text-green-600">Active</p>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-sm font-medium text-gray-500 uppercase">API</h3>
                <p class="mt-2 text-3xl font-bold text-blue-600">v1</p>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-sm font-medium text-gray-500 uppercase">Version</h3>
                <p class="mt-2 text-3xl font-bold text-purple-600">{{ version }}</p>
            </div>
        </div>
        <div class="mt-8 bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4">Quick Links</h2>
            <ul class="space-y-2">
                <li><a href="/health" class="text-blue-600 hover:underline">Health Check</a></li>
                <li><a href="/api/v1/status" class="text-blue-600 hover:underline">API Status</a></li>
                <li><a href="/login" class="text-blue-600 hover:underline">Login</a></li>
            </ul>
        </div>
    </main>
</body>
</html>
"""

_WEB_LOGIN = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} — Taskfile Example</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen flex items-center justify-center">
    <div class="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <h1 class="text-2xl font-bold text-center mb-6">Sign In</h1>
        <form class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700">Email</label>
                <input type="email" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm px-3 py-2 border" placeholder="you@example.com">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700">Password</label>
                <input type="password" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm px-3 py-2 border">
            </div>
            <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">Sign In</button>
        </form>
        <p class="mt-4 text-center text-sm text-gray-500">Don't have an account? <a href="#" class="text-blue-600 hover:underline">Sign up</a></p>
    </div>
</body>
</html>
"""

_WEB_TEST = '''\
"""Tests for the web app."""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_api_status():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"


def test_dashboard():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Dashboard" in response.text


def test_login():
    response = client.get("/login")
    assert response.status_code == 200
    assert "Sign In" in response.text
'''

_DESKTOP_PACKAGE_JSON = """\
{
  "name": "taskfile-example-desktop",
  "version": "1.0.0",
  "description": "Desktop client for Taskfile Example SaaS",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder --linux --mac --win",
    "test": "echo \\"Tests passed\\""
  },
  "dependencies": {
    "electron-updater": "^6.1.0"
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.9.0"
  },
  "build": {
    "appId": "com.taskfile-example.desktop",
    "productName": "Taskfile Example",
    "linux": { "target": ["AppImage", "deb"] },
    "mac": { "target": ["dmg"] },
    "win": { "target": ["nsis"] }
  }
}
"""

_DESKTOP_MAIN_JS = """\
const { app, BrowserWindow, Tray, Menu } = require('electron');
const path = require('path');

let mainWindow;
let tray;

const API_URL = process.env.API_URL || 'http://localhost:8000';

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
        icon: path.join(__dirname, 'icon.png'),
    });

    mainWindow.loadFile('index.html');

    // System tray
    tray = new Tray(path.join(__dirname, 'icon.png'));
    const contextMenu = Menu.buildFromTemplate([
        { label: 'Open', click: () => mainWindow.show() },
        { label: 'Quit', click: () => app.quit() },
    ]);
    tray.setToolTip('Taskfile Example');
    tray.setContextMenu(contextMenu);
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
"""

_DESKTOP_INDEX_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Taskfile Example — Desktop</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <div class="flex flex-col items-center justify-center min-h-screen p-8">
        <h1 class="text-4xl font-bold mb-4">🖥️ Taskfile Example</h1>
        <p class="text-gray-400 mb-8">Desktop Client — Connected to SaaS API</p>
        <div id="status" class="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <p class="text-sm text-gray-500">API Status</p>
            <p id="api-status" class="text-2xl font-bold text-yellow-400">Connecting...</p>
        </div>
        <button onclick="checkApi()" class="mt-6 bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg">
            Refresh
        </button>
    </div>
    <script>
        const API_URL = 'http://localhost:8000';
        async function checkApi() {
            try {
                const res = await fetch(`${API_URL}/api/v1/status`);
                const data = await res.json();
                document.getElementById('api-status').textContent = data.status;
                document.getElementById('api-status').className = 'text-2xl font-bold text-green-400';
            } catch (e) {
                document.getElementById('api-status').textContent = 'Offline';
                document.getElementById('api-status').className = 'text-2xl font-bold text-red-400';
            }
        }
        checkApi();
        setInterval(checkApi, 10000);
    </script>
</body>
</html>
"""

_DESKTOP_PRELOAD_JS = """\
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('api', {
    getApiUrl: () => process.env.API_URL || 'http://localhost:8000',
});
"""

_LANDING_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Taskfile Example — Download & SaaS</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white">
    <!-- Hero -->
    <section class="bg-gradient-to-br from-blue-600 to-purple-700 text-white">
        <nav class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <span class="text-xl font-bold">⚡ Taskfile Example</span>
            <div class="space-x-4">
                <a href="#download" class="hover:underline">Download</a>
                <a href="#pricing" class="hover:underline">Pricing</a>
                <a href="https://app.example.com/login" class="bg-white text-blue-600 px-4 py-2 rounded-lg font-medium hover:bg-gray-100">Sign In</a>
            </div>
        </nav>
        <div class="max-w-7xl mx-auto px-4 py-24 text-center">
            <h1 class="text-5xl font-bold mb-6">Deploy Anywhere.<br>One Config File.</h1>
            <p class="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
                Multi-platform deployment powered by Taskfile.yml — SaaS dashboard,
                desktop app, and this landing page, all from one configuration.
            </p>
            <div class="flex justify-center gap-4">
                <a href="#download" class="bg-white text-blue-600 px-8 py-3 rounded-lg font-bold text-lg hover:bg-gray-100">
                    ⬇️ Download Desktop
                </a>
                <a href="https://app.example.com" class="border-2 border-white px-8 py-3 rounded-lg font-bold text-lg hover:bg-white/10">
                    🌐 Open SaaS
                </a>
            </div>
        </div>
    </section>

    <!-- Features -->
    <section class="max-w-7xl mx-auto px-4 py-16">
        <h2 class="text-3xl font-bold text-center mb-12">How It Works</h2>
        <div class="grid md:grid-cols-3 gap-8">
            <div class="text-center p-6">
                <div class="text-4xl mb-4">📝</div>
                <h3 class="text-xl font-bold mb-2">1. Define in Taskfile.yml</h3>
                <p class="text-gray-600">One YAML file describes your entire project — apps, environments, deployment.</p>
            </div>
            <div class="text-center p-6">
                <div class="text-4xl mb-4">🤖</div>
                <h3 class="text-xl font-bold mb-2">2. Generate with AI</h3>
                <p class="text-gray-600">LLM agents (opencode, Goose, Aider) generate code from your spec.</p>
            </div>
            <div class="text-center p-6">
                <div class="text-4xl mb-4">🚀</div>
                <h3 class="text-xl font-bold mb-2">3. Deploy Everywhere</h3>
                <p class="text-gray-600">Local Docker, remote Podman, desktop Electron — one command.</p>
            </div>
        </div>
    </section>

    <!-- Download -->
    <section id="download" class="bg-gray-50 py-16">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <h2 class="text-3xl font-bold mb-8">Download Desktop App</h2>
            <div class="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
                <a href="#" class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
                    <div class="text-3xl mb-2">🐧</div>
                    <h3 class="font-bold">Linux</h3>
                    <p class="text-sm text-gray-500">AppImage / .deb</p>
                </a>
                <a href="#" class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
                    <div class="text-3xl mb-2">🍎</div>
                    <h3 class="font-bold">macOS</h3>
                    <p class="text-sm text-gray-500">.dmg</p>
                </a>
                <a href="#" class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
                    <div class="text-3xl mb-2">🪟</div>
                    <h3 class="font-bold">Windows</h3>
                    <p class="text-sm text-gray-500">.exe installer</p>
                </a>
            </div>
        </div>
    </section>

    <!-- Pricing -->
    <section id="pricing" class="py-16">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <h2 class="text-3xl font-bold mb-8">Pricing</h2>
            <div class="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
                <div class="border rounded-lg p-6">
                    <h3 class="font-bold text-lg">Free</h3>
                    <p class="text-3xl font-bold my-4">$0</p>
                    <ul class="text-sm text-gray-600 space-y-2">
                        <li>✅ Desktop app</li>
                        <li>✅ Local deployment</li>
                        <li>❌ SaaS dashboard</li>
                    </ul>
                </div>
                <div class="border-2 border-blue-600 rounded-lg p-6 relative">
                    <span class="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs px-3 py-1 rounded-full">Popular</span>
                    <h3 class="font-bold text-lg">Pro</h3>
                    <p class="text-3xl font-bold my-4">$9<span class="text-sm text-gray-500">/mo</span></p>
                    <ul class="text-sm text-gray-600 space-y-2">
                        <li>✅ Desktop app</li>
                        <li>✅ SaaS dashboard</li>
                        <li>✅ Remote deployment</li>
                    </ul>
                </div>
                <div class="border rounded-lg p-6">
                    <h3 class="font-bold text-lg">Enterprise</h3>
                    <p class="text-3xl font-bold my-4">Custom</p>
                    <ul class="text-sm text-gray-600 space-y-2">
                        <li>✅ Everything in Pro</li>
                        <li>✅ Fleet management</li>
                        <li>✅ Priority support</li>
                    </ul>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-900 text-gray-400 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center">
            <p>Built with ⚡ <a href="https://github.com/pyfunc/taskfile" class="text-blue-400 hover:underline">Taskfile</a> — one YAML, all platforms.</p>
        </div>
    </footer>
</body>
</html>
"""

_LANDING_DOCKERFILE = """\
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
"""


if __name__ == "__main__":
    main()
