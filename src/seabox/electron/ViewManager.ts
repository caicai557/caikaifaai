import { BrowserView, BrowserWindow, ipcMain, session } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'
import { storeManager } from './StoreManager'

// ESM compatibility: __dirname is not available in ES modules
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export class ViewManager {
    private window: BrowserWindow
    private views: Map<string, BrowserView> = new Map()
    private _currentViewId: string | null = null
    private sidebarWidth: number = 300

    private preloadPath: string

    constructor(window: BrowserWindow) {
        this.window = window
        this.preloadPath = path.join(__dirname, 'preload.mjs')

        this.setupIPC()
        this.setupResizeListener()
    }

    private setupResizeListener() {
        this.window.on('resize', () => {
            this.updateAllViewsBounds()
        })
    }

    private updateAllViewsBounds() {
        const bounds = this.window.getContentBounds()
        for (const view of this.views.values()) {
            view.setBounds({
                x: this.sidebarWidth,
                y: 0,
                width: bounds.width - this.sidebarWidth,
                height: bounds.height
            })
        }
    }

    get currentViewId(): string | null {
        return this._currentViewId
    }

    private setupIPC() {
        ipcMain.on('switch-view', (_, viewId: string) => {
            this.switchView(viewId)
        })

        ipcMain.on('update-sidebar-width', (_, width: number) => {
            this.sidebarWidth = width
            this.updateAllViewsBounds()
        })

        // Context Menu Actions
        ipcMain.on('menu:refresh', (_, id: string) => {
            this.refreshView(id)
        })

        ipcMain.on('menu:hibernate', (_, id: string) => {
            this.hibernateView(id)
        })

        ipcMain.on('menu:delete', (_, id: string) => {
            this.deleteView(id)
        })

        ipcMain.on('menu:pin', (_, id: string) => {
            storeManager.togglePin(id)
        })

        ipcMain.on('menu:rename', (_, { id, label }: { id: string, label: string }) => {
            storeManager.renameTelegram(id, label)
        })
    }

    refreshView(id: string) {
        const view = this.views.get(id)
        if (view) {
            view.webContents.reload()
            console.log(`[ViewManager] Refreshed view: ${id}`)
        }
    }

    hibernateView(id: string) {
        const view = this.views.get(id)
        if (view) {
            // Remove from window and destroy
            if (this._currentViewId === id) {
                this.window.setBrowserView(null)
                this._currentViewId = null
            }
            view.webContents.close()
            this.views.delete(id)
            console.log(`[ViewManager] Hibernated view: ${id}`)
        }
    }

    deleteView(id: string) {
        // First hibernate if exists
        this.hibernateView(id)
        // Remove from store
        storeManager.removeTelegram(id)
        console.log(`[ViewManager] Deleted view: ${id}`)
    }

    /**
     * Create a BrowserView with isolated session
     * @param id - Unique identifier for this view
     * @param url - URL to load
     * @param partition - Session partition string (e.g., 'persist:telegram-default')
     */
    createView(id: string, url: string, partition: string) {
        if (this.views.has(id)) return

        // Create isolated session using partition
        const ses = session.fromPartition(partition)

        const view = new BrowserView({
            webPreferences: {
                session: ses,
                preload: this.preloadPath,
                nodeIntegration: false,
                contextIsolation: true,
            }
        })

        view.webContents.loadURL(url)
        this.views.set(id, view)

        console.log(`[ViewManager] Created view '${id}' with partition '${partition}'`)
    }

    switchView(id: string) {
        if (id === 'home' || id === 'settings' || id === 'custom') {
            // Show React App (Remove BrowserView)
            this.window.setBrowserView(null)
            this._currentViewId = null
            return
        }

        // Check if view already exists
        if (!this.views.has(id)) {
            // Lazy create - look up partition from StoreManager
            if (id.startsWith('telegram')) {
                const instances = storeManager.getTelegramInstances()
                const instance = instances.find(t => t.id === id)

                if (instance) {
                    this.createView(id, 'https://web.telegram.org/a/', instance.partition)
                } else {
                    // Fallback for unknown telegram id
                    console.warn(`[ViewManager] Unknown telegram instance: ${id}, using default partition`)
                    this.createView(id, 'https://web.telegram.org/a/', `persist:${id}`)
                }
            }
        }

        const targetView = this.views.get(id)
        if (targetView) {
            this.window.setBrowserView(targetView)

            const bounds = this.window.getContentBounds()
            targetView.setBounds({
                x: this.sidebarWidth,
                y: 0,
                width: bounds.width - this.sidebarWidth,
                height: bounds.height
            })

            targetView.setAutoResize({ width: true, height: true })
            this._currentViewId = id
        }
    }
}

