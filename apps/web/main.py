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
