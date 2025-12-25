import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'

interface ContextMenuProps {
    x: number
    y: number
    targetId: string
    targetLabel: string
    isHibernated?: boolean
    isPinned?: boolean
    onClose: () => void
    onRefresh: (id: string) => void
    onHibernate: (id: string) => void
    onDelete: (id: string) => void
    onPin: (id: string) => void
    onRename: (id: string) => void
}

const menuItems = [
    { id: 'refresh', label: '刷新', icon: '🔄' },
    { id: 'hibernate', label: '休眠', icon: '💤', toggleLabel: '唤醒', toggleIcon: '☀️' },
    { id: 'delete', label: '删除', icon: '🗑️', danger: true },
    { id: 'pin', label: '置顶', icon: '📌', toggleLabel: '取消置顶' },
    { id: 'rename', label: '编辑名称', icon: '✏️' },
]

export function ContextMenu({
    x, y, targetId, targetLabel, isHibernated, isPinned,
    onClose, onRefresh, onHibernate, onDelete, onPin, onRename
}: ContextMenuProps) {
    const menuRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
                onClose()
            }
        }
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose()
        }

        document.addEventListener('mousedown', handleClickOutside)
        document.addEventListener('keydown', handleEscape)
        return () => {
            document.removeEventListener('mousedown', handleClickOutside)
            document.removeEventListener('keydown', handleEscape)
        }
    }, [onClose])

    const handleAction = (action: string) => {
        console.log('[ContextMenu] handleAction:', action, 'for target:', targetId)
        switch (action) {
            case 'refresh': onRefresh(targetId); break
            case 'hibernate': onHibernate(targetId); break
            case 'delete': onDelete(targetId); break
            case 'pin': onPin(targetId); break
            case 'rename': onRename(targetId); break
        }
        onClose()
    }

    return createPortal(
        <div
            ref={menuRef}
            className="fixed z-50 bg-white/80 backdrop-blur-2xl rounded-xl shadow-[0_8px_32px_rgba(0,0,0,0.12)] border border-white/20 ring-1 ring-black/5 py-1.5 min-w-[180px] origin-top-left animate-in fade-in zoom-in-95 duration-150"
            style={{ left: x, top: y, fontFamily: 'var(--font-sans)' }}
        >
            {/* Header */}
            <div className="px-3 py-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-widest border-b border-gray-100/50 mb-1 select-none">
                {targetLabel}
            </div>

            {menuItems.map((item) => {
                // Skip refresh if hibernated
                if (item.id === 'refresh' && isHibernated) return null

                const label = item.id === 'hibernate' && isHibernated ? item.toggleLabel :
                    item.id === 'pin' && isPinned ? item.toggleLabel : item.label
                const icon = item.id === 'hibernate' && isHibernated ? item.toggleIcon : item.icon

                return (
                    <button
                        key={item.id}
                        onClick={() => handleAction(item.id)}
                        className={`
                            w-full px-3 py-1.5 flex items-center gap-3 text-[13px] font-medium transition-colors duration-100
                            ${item.danger
                                ? 'text-red-600 hover:bg-red-50 active:bg-red-100'
                                : 'text-gray-700 hover:bg-blue-500 hover:text-white active:bg-blue-600'
                            }
                        `}
                    >
                        <span className="text-[15px] opactiy-80 w-5 text-center">{icon}</span>
                        <span>{label}</span>
                    </button>
                )
            })}
        </div>,
        document.body
    )
}
