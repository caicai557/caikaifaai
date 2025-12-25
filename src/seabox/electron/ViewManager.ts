import { BrowserView, BrowserWindow, ipcMain } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'

// ESM compatibility: __dirname is not available in ES modules
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
export class ViewManager {
    private window: BrowserWindow
    private views: Map<string, BrowserView> = new Map()
    private _currentViewId: string | null = null

    // Preload path (adjust based on build structure)
    // In dev: src/preload/index.ts (but compiled to out/preload/index.js)
    // electron-vite defines __dirname for preload differently usually.
    private preloadPath: string

    constructor(window: BrowserWindow) {
        this.window = window
        // This relies on electron-vite structure which exposes preload path
        // Assuming main.ts does `win = new BrowserWindow({ webPreferences: { preload: ... } })`
        // We can reuse that path or reconstruct it.
        // simpler: pass it in or use standard location
        this.preloadPath = path.join(__dirname, 'preload.mjs') // Same as main.ts usage

        this.setupIPC()
    }

    /** Get the current active view ID */
    get currentViewId(): string | null {
        return this._currentViewId
    }

    private setupIPC() {
        ipcMain.on('switch-view', (_, viewId: string) => {
            this.switchView(viewId)
        })
    }

    createView(id: string, url: string, userAgent?: string) {
        if (this.views.has(id)) return

        const view = new BrowserView({
            webPreferences: {
                preload: this.preloadPath,
                nodeIntegration: false,
                contextIsolation: true,
            }
        })

        view.webContents.loadURL(url)
        if (userAgent) view.webContents.setUserAgent(userAgent)

        // Inject custom CSS/JS for translation here (or in preload)
        // We already have 64k architecture for injection in message_interceptor
        // Ideally we re-use that logic via preload calling Python.

        this.views.set(id, view)
    }

    switchView(id: string) {
        if (id === 'home' || id === 'settings' || id === 'custom') {
            // Show React App (Remove BrowserView)
            this.window.setBrowserView(null)
            this._currentViewId = null
            return
        }

        const view = this.views.get(id)
        if (!view) {
            // Lazy create
            if (id === 'telegram') this.createView(id, 'https://web.telegram.org/a/')
            if (id === 'whatsapp') this.createView(id, 'https://web.whatsapp.com/')
            if (id === 'tiktok') this.createView(id, 'https://www.tiktok.com/')
        }

        const targetView = this.views.get(id)
        if (targetView) {
            this.window.setBrowserView(targetView)
            // Resize
            const bounds = this.window.getBounds()
            // Sidebar width is w-64 (16rem = 256px), frameless window so no title bar offset
            targetView.setBounds({ x: 256, y: 0, width: bounds.width - 256, height: bounds.height })
            targetView.setAutoResize({ width: true, height: true })
            this._currentViewId = id
        }
    }
}
