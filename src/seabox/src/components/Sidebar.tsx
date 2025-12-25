import React, { useState } from 'react'
import { ContextMenu } from './ContextMenu'

interface TelegramInstance {
    id: string
    label: string
    partition: string
    isPinned?: boolean
    isHibernated?: boolean
}

interface SidebarProps {
    setView: (id: string) => void
    width: number
    onResizeStart: () => void
    telegramInstances: TelegramInstance[]
    onAddTelegram: () => void
}

interface MenuItem {
    id: string
    label: string
    subLabel: string
    icon: React.ReactNode
    color: string
    isPinned?: boolean
}

const Icons = {
    Home: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8">
            <path d="M11.47 3.84a.75.75 0 011.06 0l8.635 8.635a.75.75 0 01-1.06 1.06l-.315-.315V20.25a2.25 2.25 0 01-2.25 2.25H6.75a2.25 2.25 0 01-2.25-2.25V13.22l-.315.315a.75.75 0 01-1.06-1.06l8.345-8.345z" />
        </svg>
    ),
    Telegram: (
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full p-1.5">
            <path d="M20.665 3.717l-17.73 6.837c-1.21.486-1.203 1.161-.222 1.462l4.552 1.42l10.532-6.645c.498-.303.953-.14.579.192l-8.533 7.701h-.002l-.002.001l-.322 3.868c.028.32.222.484.453.593c.27.128.55.076.78-.153l2.327-2.073l3.654 2.813c1.28.98 2.374.475 2.766-1.55l5.003-23.535c.618-2.614-1.28-3.693-3.232-2.79z" />
        </svg>
    ),
    Plus: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8">
            <path fillRule="evenodd" d="M12 3.75a.75.75 0 01.75.75v6.75h6.75a.75.75 0 010 1.5h-6.75v6.75a.75.75 0 01-1.5 0v-6.75H4.5a.75.75 0 010-1.5h6.75V4.5a.75.75 0 01.75-.75z" clipRule="evenodd" />
        </svg>
    )
}

export default function Sidebar({ setView, width, onResizeStart, telegramInstances, onAddTelegram }: SidebarProps): React.ReactElement {
    const [activeId, setActiveId] = useState('home')

    // Context menu state
    const [contextMenu, setContextMenu] = useState<{
        visible: boolean
        x: number
        y: number
        targetId: string
        targetLabel: string
        isHibernated?: boolean
        isPinned?: boolean
    } | null>(null)

    const handleContextMenu = (e: React.MouseEvent, item: MenuItem & { isHibernated?: boolean, isPinned?: boolean }) => {
        console.log('[Sidebar] handleContextMenu called for:', item.id, item)
        // Only show context menu for telegram items
        if (item.id === 'home') {
            console.log('[Sidebar] Skipping context menu for home')
            return
        }
        e.preventDefault()
        console.log('[Sidebar] Setting context menu state at:', e.clientX, e.clientY)
        setContextMenu({
            visible: true,
            x: e.clientX,
            y: e.clientY,
            targetId: item.id,
            targetLabel: item.label,
            isHibernated: item.isHibernated,
            isPinned: item.isPinned
        })
    }

    // Window Controls
    const handleWindowControl = (action: 'minimize' | 'maximize' | 'close') => {
        if (window.ipcRenderer) window.ipcRenderer.send(`window:${action}`)
    }

    const handleRefresh = (id: string) => {
        console.log('[Sidebar] handleRefresh:', id)
        if (window.ipcRenderer) window.ipcRenderer.send('menu:refresh', id)
    }
    const handleHibernate = (id: string) => {
        console.log('[Sidebar] handleHibernate:', id)
        if (window.ipcRenderer) window.ipcRenderer.send('menu:hibernate', id)
    }
    const handleDelete = (id: string) => {
        console.log('[Sidebar] handleDelete:', id)
        if (confirm(`确定要删除 ${id} 吗？`)) {
            if (window.ipcRenderer) window.ipcRenderer.send('menu:delete', id)
        }
    }
    const handlePin = (id: string) => {
        console.log('[Sidebar] handlePin:', id)
        if (window.ipcRenderer) window.ipcRenderer.send('menu:pin', id)
    }
    const handleRename = (id: string) => {
        console.log('[Sidebar] handleRename:', id)
        const newName = prompt('输入新名称:')
        if (newName) {
            if (window.ipcRenderer) window.ipcRenderer.send('menu:rename', { id, label: newName })
        }
    }

    // Build menu items from props - include isPinned and isHibernated for context menu
    const menuItems: (MenuItem & { isHibernated?: boolean; isPinned?: boolean })[] = [
        { id: 'home', label: '仪表盘', subLabel: '系统概览', icon: Icons.Home, color: 'bg-blue-600' },
        ...telegramInstances.map((instance, i) => ({
            id: instance.id,
            label: instance.label,
            subLabel: i === 0 ? '官方频道' : `备用账号 ${i}`,
            icon: Icons.Telegram,
            color: 'bg-[#0088cc]',
            isPinned: instance.isPinned,
            isHibernated: instance.isHibernated
        }))
    ]

    const handleSetView = (id: string) => {
        setActiveId(id)
        setView(id)
    }

    return (
        <div
            className="relative h-screen flex flex-col font-sans select-none shrink-0 @container/sidebar mica-background"
            style={{ width }}
        >
            {/* Logo Area - DRAG REGION */}
            <div className={`
                drag-region
                p-3 @[150px]/sidebar:p-6 @[150px]/sidebar:pb-4 
                transition-all duration-300
                relative
            `}>
                {/* Traffic Lights (Window Controls) */}
                <div className="flex items-center gap-2 mb-4 pl-1 no-drag group/lights opacity-0 hover:opacity-100 transition-opacity absolute top-3 right-3 z-50 @[150px]/sidebar:relative @[150px]/sidebar:top-auto @[150px]/sidebar:right-auto @[150px]/sidebar:opacity-100 @[150px]/sidebar:mb-6 @[150px]/sidebar:pl-0 @[150px]/sidebar:justify-end">
                    <button onClick={() => handleWindowControl('close')} className="w-3.5 h-3.5 rounded-full bg-[#FF5F56] border border-[#E0443E] flex items-center justify-center group/btn shadow-sm active:scale-90 transition-transform">
                        <svg className="w-2.5 h-2.5 text-black/50 opacity-0 group-hover/btn:opacity-100" viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" /></svg>
                    </button>
                    <button onClick={() => handleWindowControl('minimize')} className="w-3.5 h-3.5 rounded-full bg-[#FFBD2E] border border-[#DEA123] flex items-center justify-center group/btn shadow-sm active:scale-90 transition-transform">
                        <svg className="w-2.5 h-2.5 text-black/50 opacity-0 group-hover/btn:opacity-100" viewBox="0 0 24 24" fill="currentColor"><path d="M19 13H5v-2h14v2z" /></svg>
                    </button>
                    <button onClick={() => handleWindowControl('maximize')} className="w-3.5 h-3.5 rounded-full bg-[#27C93F] border border-[#1AAB29] flex items-center justify-center group/btn shadow-sm active:scale-90 transition-transform">
                        <svg className="w-2.5 h-2.5 text-black/50 opacity-0 group-hover/btn:opacity-100" viewBox="0 0 24 24" fill="currentColor"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" /></svg>
                    </button>
                </div>

                <div className="flex items-center justify-center @[150px]/sidebar:justify-start gap-3 mb-2 min-w-0">
                    <div className="w-8 h-8 @[150px]/sidebar:w-10 @[150px]/sidebar:h-10 bg-gradient-to-b from-blue-500 to-blue-600 rounded-[10px] flex items-center justify-center text-white shadow-lg shadow-blue-500/20 shrink-0 transition-all duration-300">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 @[150px]/sidebar:w-6 @[150px]/sidebar:h-6 drop-shadow-sm">
                            <path fillRule="evenodd" d="M12.963 2.286a.75.75 0 00-1.071-.136 9.742 9.742 0 00-3.539 6.177 7.547 7.547 0 01-1.705-1.715.75.75 0 00-1.152-.082A9.735 9.735 0 002.25 12c0 2.135.634 4.115 1.717 5.766a.75.75 0 001.109-.123 7.548 7.548 0 011.411-1.921 7.547 7.547 0 011.96 1.405.75.75 0 001.144-.09 9.74 9.74 0 002.508-6.166 7.546 7.546 0 012.35 1.543.75.75 0 001.096-.067 9.74 9.74 0 002.321-6.195 7.546 7.546 0 012.006 1.139.75.75 0 001.071-.165 9.736 9.736 0 002.057-6.52.75.75 0 00-.518-.707c-2.42-.713-4.908-1.572-7.42-2.316a.75.75 0 00-.737.143z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <div className="hidden @[150px]/sidebar:block min-w-0 overflow-hidden">
                        <h1 className="text-[17px] font-semibold text-[var(--text-primary)] tracking-tight leading-tight truncate">SeaBox</h1>
                        <p className="text-[11px] text-[var(--text-secondary)] font-medium tracking-normal uppercase truncate">Telegram Fleet</p>
                    </div>
                </div>
            </div>

            {/* Menu List - iPadOS STYLE */}
            <nav className="flex-1 px-2 @[150px]/sidebar:px-3 space-y-1 overflow-y-auto overflow-x-hidden no-drag">
                {menuItems.map((item) => {
                    const isActive = activeId === item.id
                    return (
                        <div
                            key={item.id}
                            onClick={() => handleSetView(item.id)}
                            onContextMenu={(e) => handleContextMenu(e, item)}
                            className={`
                                group relative w-full flex items-center justify-center @[150px]/sidebar:justify-start
                                p-1.5 @[150px]/sidebar:px-2.5 @[150px]/sidebar:py-2
                                rounded-lg cursor-pointer transition-all duration-200 ease-out apple-ease min-w-0
                                ${isActive
                                    ? 'bg-[var(--bg-sidebar-active)]'
                                    : 'hover:bg-[var(--bg-sidebar-active)] active:scale-[0.98]'
                                }
                            `}
                        >
                            {/* Icon - SF Symbols Style */}
                            <div className={`
                                w-7 h-7 flex items-center justify-center shrink-0 transition-colors duration-200
                                ${isActive ? 'text-[var(--accent-blue)]' : 'text-gray-500 group-hover:text-gray-700'}
                            `}>
                                {item.icon}
                            </div>

                            {/* Text Content */}
                            <div className="hidden @[150px]/sidebar:flex flex-col min-w-0 ml-3 overflow-hidden">
                                <span className={`
                                    text-[14px] font-medium truncate leading-tight transition-colors
                                    ${isActive ? 'text-[var(--text-primary)] font-semibold' : 'text-[var(--text-primary)] opacity-80'}
                                `}>
                                    {item.label}
                                </span>
                            </div>

                            {/* Status Indicators (Pin/Hibernate) */}
                            {item.isPinned && (
                                <div className="absolute right-2 w-1.5 h-1.5 rounded-full bg-gray-300 hidden @[150px]/sidebar:block" />
                            )}
                        </div>
                    )
                })}

                {/* ADD BUTTON - Minimalist */}
                <div
                    onClick={onAddTelegram}
                    className="
                        group w-full flex items-center justify-center @[150px]/sidebar:justify-start 
                        mt-4
                        p-2 
                        rounded-lg cursor-pointer transition-all duration-200 apple-ease
                        hover:bg-[var(--bg-sidebar-active)] active:scale-[0.98]
                    "
                >
                    <div className="w-7 h-7 flex items-center justify-center shrink-0 text-gray-400 group-hover:text-gray-600">
                        {Icons.Plus}
                    </div>
                    <div className="hidden @[150px]/sidebar:flex flex-col min-w-0 ml-3">
                        <span className="text-[14px] font-medium opacity-70 group-hover:opacity-100 transition-opacity">Add Account</span>
                    </div>
                </div>
            </nav>

            {/* Bottom Section - User Profile Style */}
            <div className="p-3 @[150px]/sidebar:p-3 border-t border-[var(--separator)] overflow-hidden no-drag">
                <button className="
                    w-full min-w-0 group 
                    flex items-center justify-center @[150px]/sidebar:justify-start
                    p-1.5 @[150px]/sidebar:px-2.5 @[150px]/sidebar:py-2
                    rounded-lg
                    hover:bg-[var(--bg-sidebar-active)] transition-all duration-200 apple-ease active:scale-[0.98]
                ">
                    <div className="
                        w-7 h-7 
                        rounded-full bg-slate-200 flex items-center justify-center text-gray-500 shrink-0
                    ">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 group-hover:rotate-45 transition-transform duration-500 ease-out">
                            <path fillRule="evenodd" d="M11.078 2.25c-.917 0-1.699.663-1.85 1.567L9.05 4.889c-.02.12-.115.26-.297.348a7.493 7.493 0 00-.986.64c-.166.121-.338.126-.45.06l-1.653-.95a1.883 1.883 0 00-1.897.108c-.754.495-1.127 1.34-1.332 2.196l-.37 1.547a1.887 1.887 0 001.073 2.133L5.3 12l-2.146 1.026a1.887 1.887 0 00-1.073 2.133l.37 1.548c.205.856.578 1.7 1.332 2.196a1.883 1.883 0 001.897.108l1.653-.95c.112-.066.284-.06.45.06.315.228.647.442.986.64.182.088.277.228.297.348l.178 1.072c.151.904.933 1.567 1.85 1.567h3.044c.917 0 1.699-.663 1.85-1.567l.178-1.072c.02-.12.115-.26.297-.348.339-.199.671-.412.986-.64.166-.121.338-.126.45-.06l1.653.95a1.883 1.883 0 001.897-.108c.754-.496 1.127-1.34 1.332-2.196l.37-1.548a1.887 1.887 0 00-1.073-2.133L18.7 12l2.146-1.026a1.887 1.887 0 001.073-2.133l-.37-1.547c-.205-.856-.578-1.7-1.332-2.196a1.883 1.883 0 00-1.897-.108l-1.653.95c-.112.066-.284.06-.45-.06a7.493 7.493 0 00-.986-.64c-.182-.088-.277-.228-.297-.348l-.178-1.072c-.151-.904-.933-1.567-1.85-1.567h-3.044zM12 15.75a3.75 3.75 0 100-7.5 3.75 3.75 0 000 7.5z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <div className="hidden @[150px]/sidebar:block text-left leading-tight min-w-0 overflow-hidden ml-3">
                        <div className="font-semibold text-[var(--text-primary)] text-[13px] truncate">Admin</div>
                        <div className="text-[11px] text-[var(--text-secondary)] truncate">SeaBox v1.0.5</div>
                    </div>
                </button>
            </div>

            {/* RESIZE HANDLE */}
            <div
                className="absolute top-0 right-0 w-[4px] h-full cursor-col-resize hover:bg-blue-400/30 transition-colors z-50 active:bg-blue-500"
                onMouseDown={onResizeStart}
            />

            {/* CONTEXT MENU */}
            {contextMenu && (
                <ContextMenu
                    x={contextMenu.x}
                    y={contextMenu.y}
                    targetId={contextMenu.targetId}
                    targetLabel={contextMenu.targetLabel}
                    isHibernated={contextMenu.isHibernated}
                    isPinned={contextMenu.isPinned}
                    onClose={() => setContextMenu(null)}
                    onRefresh={handleRefresh}
                    onHibernate={handleHibernate}
                    onDelete={handleDelete}
                    onPin={handlePin}
                    onRename={handleRename}
                />
            )}
        </div>
    )
}
