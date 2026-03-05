# Generate: Desktop Application (Electron)

## Context
You are generating an Electron desktop application that connects to the SaaS web API.
The project is managed by Taskfile.yml — builds produce Linux/macOS/Windows packages.

## Requirements

### Tech Stack
- **Framework**: Electron 28+
- **Language**: JavaScript (main process) + HTML/TailwindCSS (renderer)
- **Builder**: electron-builder
- **Auto-update**: electron-updater

### Features
1. Main window showing connection status to SaaS API
2. System tray icon with "Open" and "Quit" options
3. Auto-check API status every 10 seconds
4. Offline indicator when API unreachable
5. Cross-platform: Linux (AppImage, .deb), macOS (.dmg), Windows (.exe)

### File Structure
```
apps/desktop/
├── package.json         # npm deps + electron-builder config
├── main.js             # Electron main process
├── preload.js          # Context bridge
├── index.html          # Renderer (TailwindCSS CDN)
└── icon.png            # App icon (placeholder)
```

### API Integration
- Connect to `http://localhost:8000/api/v1/status`
- Show green/red status indicator
- Display API version and features list

### Constraints
- Must use contextIsolation: true
- No nodeIntegration in renderer
- Use contextBridge for API URL
