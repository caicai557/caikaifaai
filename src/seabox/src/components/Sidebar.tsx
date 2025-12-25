import React from 'react'

interface SidebarProps {
    setView: (id: string) => void
}

interface MenuItem {
    id: string
    label: string
    icon: string
}

export default function Sidebar({ setView }: SidebarProps): React.ReactElement {
    const menuItems: MenuItem[] = [
        { id: 'home', label: '首页', icon: '🐶' },
        { id: 'whatsapp', label: 'WhatsApp', icon: '💬' },
        { id: 'telegram', label: 'Telegram', icon: '✈️' },
        { id: 'tiktok', label: 'TikTok', icon: '🎵' },
        { id: 'custom', label: 'Custom Web', icon: '🌐' },
    ]

    return (
        <div className="w-64 bg-white h-screen border-r border-gray-200 flex flex-col">
            <div className="p-6 flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                    S
                </div>
                <h1 className="text-xl font-bold text-gray-800">SeaBox</h1>
            </div>

            <nav className="flex-1 px-4 space-y-2">
                {menuItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => setView(item.id)}
                        className="w-full flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-blue-50 hover:text-blue-600 rounded-xl transition-colors text-left"
                    >
                        <span className="text-xl">{item.icon}</span>
                        <span className="font-medium">{item.label}</span>
                    </button>
                ))}
            </nav>

            <div className="p-4 border-t border-gray-100">
                <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-500 hover:bg-gray-50 rounded-xl">
                    <span>⚙️</span>
                    <span>翻译配置</span>
                </button>
            </div>
        </div>
    )
}
