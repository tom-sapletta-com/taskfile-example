# Generate: SaaS Web Application

## Context
You are generating a FastAPI SaaS web application as part of a multi-platform project.
The project is managed by Taskfile.yml — this app will be deployed as a Docker container.

## Requirements

### Tech Stack
- **Framework**: FastAPI (Python 3.12+)
- **UI**: Jinja2 templates + TailwindCSS (CDN) + HTMX
- **Database**: SQLite via aiosqlite
- **Auth**: JWT tokens (python-jose)

### Endpoints
1. `GET /health` — JSON health check (status, version, uptime)
2. `GET /api/v1/status` — API status for desktop client
3. `GET /` — redirect to dashboard
4. `GET /dashboard` — main dashboard (requires auth)
5. `GET /login` — login page
6. `POST /api/v1/auth/login` — JWT login
7. `GET /api/v1/auth/me` — current user info

### File Structure
```
apps/web/
├── main.py              # FastAPI app
├── requirements.txt     # Python deps
├── Dockerfile          # Production container
├── templates/
│   ├── dashboard.html
│   └── login.html
├── static/             # CSS/JS assets
└── tests/
    └── test_app.py     # pytest tests
```

### Dashboard Features
- Show project stats (status, API version, uptime)
- Quick links to API endpoints
- Responsive layout with TailwindCSS
- Modern, clean design

### Constraints
- Must expose port 8000
- Must have `/health` endpoint returning `{"status": "ok"}`
- Dockerfile must use `python:3.12-slim` base
- All templates must use TailwindCSS CDN
