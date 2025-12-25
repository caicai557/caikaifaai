import React, { useEffect, useState } from 'react'

interface Stats {
    chars: number
    expiry: string
}

export default function Home(): React.ReactElement {
    const [stats, setStats] = useState<Stats>({ chars: 0, expiry: 'Loading...' })

    useEffect(() => {
        // Fetch from Python API sidecar using relative URL or configured port
        fetch('http://127.0.0.1:8000/stats')
            .then(res => res.json())
            .then(data => {
                setStats({ chars: data.chars_available, expiry: data.expiry_date })
            })
            .catch(err => console.error("Failed to fetch stats:", err))
    }, [])

    return (
        <div className="bg-gray-50 h-full p-8 overflow-y-auto">
            <header className="flex justify-between items-center mb-8">
                <div className="bg-white px-4 py-2 rounded-lg shadow-sm text-gray-500 text-sm">
                    🕗 2025-03-26 17:48:22
                </div>
                <div className="flex bg-white rounded-lg shadow-sm p-1">
                    <button className="px-3 py-1 rounded bg-gray-100 text-gray-700 text-sm">中</button>
                    <button className="px-3 py-1 text-gray-400 text-sm">🌙</button>
                </div>
            </header>

            <section className="mb-8">
                <div className="flex items-center gap-2 mb-4 border-l-4 border-blue-500 pl-3">
                    <h2 className="text-lg font-bold text-gray-800">账户信息</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                        <div className="text-gray-400 text-sm mb-2">可用字符数</div>
                        <div className="text-3xl font-bold text-gray-800">{stats.chars}</div>
                    </div>
                    <div className="bg-white p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                        <div className="text-gray-400 text-sm mb-2">到期时间</div>
                        <div className="text-xl font-bold text-red-500">{stats.expiry}</div>
                        <div className="text-xs text-red-400 mt-1">剩余 90 天</div>
                    </div>
                    <div className="bg-white p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                        <div className="text-gray-400 text-sm mb-2">设备标识</div>
                        <div className="text-xs font-mono text-blue-500 bg-blue-50 p-2 rounded break-all">
                            f0d16988-a9ff-5a04...
                        </div>
                    </div>
                </div>
            </section>

            <section>
                <div className="flex items-center gap-2 mb-4 border-l-4 border-blue-500 pl-3">
                    <h2 className="text-lg font-bold text-gray-800">核心功能</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-blue-500 text-white p-6 rounded-2xl shadow-lg hover:opacity-90 cursor-pointer">
                        <div className="flex flex-col items-center text-center py-4">
                            <span className="text-4xl mb-4">👤</span>
                            <h3 className="font-bold text-lg mb-2">多账号同时登录</h3>
                            <p className="text-blue-100 text-sm">支持同一平台多个账号同时在线管理</p>
                        </div>
                    </div>
                    <div className="bg-green-500 text-white p-6 rounded-2xl shadow-lg hover:opacity-90 cursor-pointer">
                        <div className="flex flex-col items-center text-center py-4">
                            <span className="text-4xl mb-4">🔗</span>
                            <h3 className="font-bold text-lg mb-2">统一消息管理</h3>
                            <p className="text-green-100 text-sm">集中处理所有平台的聊天和通知</p>
                        </div>
                    </div>
                    <div className="bg-orange-500 text-white p-6 rounded-2xl shadow-lg hover:opacity-90 cursor-pointer">
                        <div className="flex flex-col items-center text-center py-4">
                            <span className="text-4xl mb-4">💬</span>
                            <h3 className="font-bold text-lg mb-2">高效沟通实时翻译</h3>
                            <p className="text-orange-100 text-sm">双向翻译支持 10+ 种语言</p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    )
}
