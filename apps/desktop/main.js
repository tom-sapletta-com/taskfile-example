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
