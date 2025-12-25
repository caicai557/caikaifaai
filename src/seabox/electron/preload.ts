import { ipcRenderer, contextBridge } from 'electron'
import { initTelegramGovernance } from './telegram-governance'

// --------- Expose some API to the Renderer process ---------
contextBridge.exposeInMainWorld('ipcRenderer', {
  on(...args: Parameters<typeof ipcRenderer.on>) {
    const [channel, listener] = args
    return ipcRenderer.on(channel, (event, ...args) => listener(event, ...args))
  },
  off(...args: Parameters<typeof ipcRenderer.off>) {
    const [channel, ...omit] = args
    return ipcRenderer.off(channel, ...omit)
  },
  send(...args: Parameters<typeof ipcRenderer.send>) {
    const [channel, ...omit] = args
    return ipcRenderer.send(channel, ...omit)
  },
  invoke(...args: Parameters<typeof ipcRenderer.invoke>) {
    const [channel, ...omit] = args
    return ipcRenderer.invoke(channel, ...omit)
  },

  // You can expose other APIs you need here.
  // ...
})

// --------- Telegram Governance Injection ---------
window.addEventListener('DOMContentLoaded', () => {
  const host = window.location.hostname
  if (host.includes('telegram') || host.includes('web.telegram.org')) {
    console.log('[SeaBox] Telegram Detected - Governance Active')
    initTelegramGovernance()
  }
})
