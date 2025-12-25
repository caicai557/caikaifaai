import React from 'react'

export default function Settings(): React.ReactElement {
    return (
        <div className="p-8 bg-gray-50 h-full">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">配置</h2>

            <div className="bg-white p-6 rounded-2xl shadow-sm mb-6">
                <h3 className="font-bold text-lg mb-4">翻译设置</h3>
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <span className="text-gray-600">源语言</span>
                        <select className="border border-gray-300 rounded px-3 py-1 bg-white text-gray-700">
                            <option>自动检测</option>
                            <option>英语</option>
                        </select>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-gray-600">目标语言</span>
                        <select className="border border-gray-300 rounded px-3 py-1 bg-white text-gray-700">
                            <option>简体中文</option>
                            <option>English</option>
                            <option>日本語</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm">
                <h3 className="font-bold text-lg mb-4">关于</h3>
                <p className="text-gray-500 text-sm">SeaBox v1.0.4 - Made with ❤️ by CaiCai</p>
            </div>
        </div>
    )
}
