import Store from 'electron-store'

// Type definitions for persisted state
export interface TelegramInstance {
    id: string          // 'telegram' | 'telegram-2' | ...
    label: string       // User-defined name
    partition: string   // Session isolation key
    isPinned?: boolean  // Pin to top of list
    isHibernated?: boolean // Memory optimization
}

export interface WindowState {
    x: number
    y: number
    width: number
    height: number
    isMaximized: boolean
}

export interface AppSettings {
    sidebar: {
        width: number
    }
    telegrams: TelegramInstance[]
    window: WindowState
}

// Default values
const defaults: AppSettings = {
    sidebar: {
        width: 300
    },
    telegrams: [
        { id: 'telegram', label: 'Telegram', partition: 'persist:telegram-default' }
    ],
    window: {
        x: 100,
        y: 100,
        width: 1400,
        height: 900,
        isMaximized: false
    }
}

class StoreManager {
    private store: Store<AppSettings>

    constructor() {
        this.store = new Store<AppSettings>({
            name: 'seabox-config',
            defaults
        })
    }

    // Sidebar Width
    getSidebarWidth(): number {
        return this.store.get('sidebar.width', defaults.sidebar.width)
    }

    setSidebarWidth(width: number): void {
        this.store.set('sidebar.width', width)
    }

    // Telegram Instances
    getTelegramInstances(): TelegramInstance[] {
        return this.store.get('telegrams', defaults.telegrams)
    }

    setTelegramInstances(instances: TelegramInstance[]): void {
        this.store.set('telegrams', instances)
    }

    addTelegramInstance(instance: TelegramInstance): void {
        const current = this.getTelegramInstances()
        current.push(instance)
        this.setTelegramInstances(current)
    }

    removeTelegramInstance(id: string): void {
        const current = this.getTelegramInstances()
        this.setTelegramInstances(current.filter(t => t.id !== id))
    }

    // Alias for ViewManager convenience
    removeTelegram(id: string): void {
        this.removeTelegramInstance(id)
    }

    togglePin(id: string): void {
        const current = this.getTelegramInstances()
        const updated = current.map(t =>
            t.id === id ? { ...t, isPinned: !t.isPinned } : t
        )
        this.setTelegramInstances(updated)
    }

    renameTelegram(id: string, newLabel: string): void {
        const current = this.getTelegramInstances()
        const updated = current.map(t =>
            t.id === id ? { ...t, label: newLabel } : t
        )
        this.setTelegramInstances(updated)
    }

    // Window State
    getWindowState(): WindowState {
        return this.store.get('window', defaults.window)
    }

    setWindowState(state: Partial<WindowState>): void {
        const current = this.getWindowState()
        this.store.set('window', { ...current, ...state })
    }

    // Full Settings (for IPC)
    getAllSettings(): AppSettings {
        return {
            sidebar: { width: this.getSidebarWidth() },
            telegrams: this.getTelegramInstances(),
            window: this.getWindowState()
        }
    }

    updateSettings(partial: Partial<AppSettings>): void {
        if (partial.sidebar?.width !== undefined) {
            this.setSidebarWidth(partial.sidebar.width)
        }
        if (partial.telegrams !== undefined) {
            this.setTelegramInstances(partial.telegrams)
        }
        if (partial.window !== undefined) {
            this.setWindowState(partial.window)
        }
    }
}

// Singleton export
export const storeManager = new StoreManager()
