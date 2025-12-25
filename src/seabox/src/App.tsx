import React, { useState } from 'react'
import Sidebar from './components/Sidebar'
import Home from './components/Home'

function App(): React.ReactElement {
    const [view, setView] = useState<string>('home')

    // In Phase 3, we use IPC to tell Main process to switch BrowserViews
    const handleViewChange = (id: string): void => {
        setView(id)
        if (window.ipcRenderer) {
            window.ipcRenderer.send('switch-view', id)
        } else {
            console.warn('IPC not available (Dev Mode or Web Browser)')
        }
    }

    return (
        <div className="flex h-screen w-screen bg-gray-100 font-sans text-gray-900 overflow-hidden">
            <Sidebar setView={handleViewChange} />
            <main className="flex-1 relative">
                {view === 'home' ? (
                    <Home />
                ) : (
                    <div className="flex items-center justify-center h-full text-gray-400">
                        <div className="text-center">
                            <div className="text-6xl mb-4">🏗️</div>
                            <h2 className="text-2xl font-bold">Connecting to {view}...</h2>
                            <p>BrowserView Loading (Phase 3)</p>
                        </div>
                    </div>
                )}
            </main>
        </div>
    )
}

export default App
