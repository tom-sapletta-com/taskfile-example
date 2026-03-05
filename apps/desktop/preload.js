const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('api', {
    getApiUrl: () => process.env.API_URL || 'http://localhost:8000',
});
