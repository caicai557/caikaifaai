import React, { useState, useCallback, useEffect, useRef } from 'react'
import Sidebar from './components/Sidebar'
import Home from './components/Home'

// Type for settings from main process
interface TelegramInstance {
    id: string
    label: string
    partition: string
    isPinned?: boolean
    isHibernated?: boolean
}

interface AppSettings {
    sidebar: { width: number }
    telegrams: TelegramInstance[]
}

function App(): React.ReactElement {
    const [view, setView] = useState<string>('home')
    const [sidebarWidth, setSidebarWidth] = useState<number>(300)
    const [telegramInstances, setTelegramInstances] = useState<TelegramInstance[]>([])
    const [isLoaded, setIsLoaded] = useState(false)
    const isResizing = useRef(false)
    const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null)

    // Load settings on mount
    useEffect(() => {
        const loadSettings = async () => {
            try {
                // Check if running in Electron environment
                if (!window.ipcRenderer) {
                    console.warn('[App] Not in Electron environment, using defaults')
                    setTelegramInstances([{ id: 'telegram', label: 'Telegram', partition: 'persist:telegram-default' }])
                    setIsLoaded(true)
                    return
                }
                const settings: AppSettings = await window.ipcRenderer.invoke('get-settings')
                setSidebarWidth(settings.sidebar.width)
                setTelegramInstances(settings.telegrams)
                // Also sync sidebar width to main process for BrowserView
                window.ipcRenderer.send('update-sidebar-width', settings.sidebar.width)
            } catch (err) {
                console.error('Failed to load settings:', err)
            } finally {
                setIsLoaded(true)
            }
        }
        loadSettings()
    }, [])

    // Save sidebar width (debounced)
    const saveSidebarWidth = useCallback((width: number) => {
        if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current)
        saveTimeoutRef.current = setTimeout(() => {
            window.ipcRenderer.invoke('set-settings', { sidebar: { width } })
        }, 500)
    }, [])

    // Handle Resize logic
    const startResizing = useCallback(() => {
        isResizing.current = true
        document.body.style.cursor = 'col-resize'
        const overlay = document.createElement('div')
        overlay.id = 'resize-overlay'
        overlay.style.position = 'fixed'
        overlay.style.inset = '0'
        overlay.style.zIndex = '9999'
        overlay.style.cursor = 'col-resize'
        document.body.appendChild(overlay)
    }, [])

    const stopResizing = useCallback(() => {
        isResizing.current = false
        document.body.style.cursor = 'default'
        document.getElementById('resize-overlay')?.remove()
    }, [])

    const resize = useCallback((e: MouseEvent) => {
        if (!isResizing.current) return

        let newWidth = e.clientX
        if (newWidth < 80) newWidth = 80
        if (newWidth > 600) newWidth = 600

        setSidebarWidth(newWidth)
        window.ipcRenderer.send('update-sidebar-width', newWidth)
        saveSidebarWidth(newWidth)
    }, [saveSidebarWidth])

    useEffect(() => {
        window.addEventListener('mousemove', resize)
        window.addEventListener('mouseup', stopResizing)
        return () => {
            window.removeEventListener('mousemove', resize)
            window.removeEventListener('mouseup', stopResizing)
        }
    }, [resize, stopResizing])

    // Handle adding new Telegram instance
    const handleAddTelegram = useCallback(() => {
        const newId = `telegram-${telegramInstances.length + 1}`
        const newInstance: TelegramInstance = {
            id: newId,
            label: `Telegram #${telegramInstances.length + 1}`,
            partition: `persist:${newId}`
        }
        const updated = [...telegramInstances, newInstance]
        setTelegramInstances(updated)
        window.ipcRenderer.invoke('set-settings', { telegrams: updated })
    }, [telegramInstances])

    const handleViewChange = (id: string): void => {
        setView(id)
        if (window.ipcRenderer) {
            window.ipcRenderer.send('switch-view', id)
        } else {
            console.warn('IPC not available (Dev Mode or Web Browser)')
        }
    }

    // Don't render until settings are loaded to prevent flash
    if (!isLoaded) {
        return (
            <div className="flex h-screen w-screen items-center justify-center bg-gray-100">
                <div className="text-gray-400">Loading...</div>
            </div>
        )
    }

    return (
        <div className="flex h-screen w-screen bg-gray-100 font-sans text-gray-900 overflow-hidden">
            <Sidebar
                setView={handleViewChange}
                width={sidebarWidth}
                onResizeStart={startResizing}
                telegramInstances={telegramInstances}
                onAddTelegram={handleAddTelegram}
            />
            <main className="flex-1 relative bg-white">
                {view === 'home' && <Home />}
            </main>
        </div>
    )
}

export default App
