import { app, BrowserWindow, ipcMain } from 'electron'
import { storeManager } from './StoreManager'

// Fix GPU errors in VM/WSL/headless environments
app.disableHardwareAcceleration()
app.commandLine.appendSwitch('disable-gpu')
app.commandLine.appendSwitch('no-sandbox')
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// The built directory structure
//
// ├─┬─┬ dist
// │ │ └── index.html
// │ │
// │ ├─┬ dist-electron
// │ │ ├── main.js
// │ │ └── preload.mjs
// │
process.env.APP_ROOT = path.join(__dirname, '..')

// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
export const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']
export const MAIN_DIST = path.join(process.env.APP_ROOT, 'dist-electron')
export const RENDERER_DIST = path.join(process.env.APP_ROOT, 'dist')

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL ? path.join(process.env.APP_ROOT, 'public') : RENDERER_DIST

let win: BrowserWindow | null

function createWindow() {
  // Restore window state from storage
  const windowState = storeManager.getWindowState()

  win = new BrowserWindow({
    icon: path.join(process.env.VITE_PUBLIC, 'electron-vite.svg'),
    x: windowState.x,
    y: windowState.y,
    width: windowState.width,
    height: windowState.height,
    webPreferences: {
      preload: path.join(__dirname, 'preload.mjs'),
    },
  })

  // Restore maximized state
  if (windowState.isMaximized) {
    win.maximize()
  }

  // Save window state on resize/move (debounced)
  let saveTimeout: NodeJS.Timeout | null = null
  const saveWindowState = () => {
    if (saveTimeout) clearTimeout(saveTimeout)
    saveTimeout = setTimeout(() => {
      if (win && !win.isDestroyed()) {
        const bounds = win.getBounds()
        storeManager.setWindowState({
          x: bounds.x,
          y: bounds.y,
          width: bounds.width,
          height: bounds.height,
          isMaximized: win.isMaximized()
        })
      }
    }, 500)
  }

  win.on('resize', saveWindowState)
  win.on('move', saveWindowState)
  win.on('maximize', saveWindowState)
  win.on('unmaximize', saveWindowState)

  // Test active push message to Renderer-process.
  win.webContents.on('did-finish-load', () => {
    win?.webContents.send('main-process-message', (new Date).toLocaleString())
  })

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL)
  } else {
    win.loadFile(path.join(RENDERER_DIST, 'index.html'))
  }
}

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
    win = null
  }
})

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

// --- Python Sidecar Logic ---
import { spawn, type ChildProcess } from 'node:child_process'

let pythonProcess: ChildProcess | null = null

function startPythonServer() {
  // Assuming .venv is in the project root (2 levels up from src/seabox)
  // APP_ROOT is src/seabox
  const pythonExec = path.join(process.env.APP_ROOT, '../../.venv/bin/python')
  const scriptPath = path.join(process.env.APP_ROOT, 'api/server.py')

  console.log('[Electron] Spawning Python Backend:', pythonExec, scriptPath)

  pythonProcess = spawn(pythonExec, [scriptPath], {
    env: { ...process.env, PORT: '8000', PYTHONUNBUFFERED: '1' },
    cwd: process.env.APP_ROOT
  })

  pythonProcess.stdout?.on('data', (data) => {
    console.log(`[Python]: ${data.toString().trim()}`)
  })

  pythonProcess.stderr?.on('data', (data) => {
    console.error(`[Python Err]: ${data.toString().trim()}`)
  })

  pythonProcess.on('error', (err) => {
    console.error('[Electron] Failed to start Python process:', err)
  })

  pythonProcess.on('exit', (code) => {
    console.log(`[Electron] Python process exited with code ${code}`)
  })
}

app.on('will-quit', () => {
  if (pythonProcess) {
    console.log('[Electron] Killing Python process...')
    pythonProcess.kill()
    pythonProcess = null
  }
})

import { ViewManager } from './ViewManager'

// IPC Handlers for settings persistence
ipcMain.handle('get-settings', () => {
  return storeManager.getAllSettings()
})

ipcMain.handle('set-settings', (_, settings: Partial<{ sidebar: { width: number }, telegrams: unknown[], window: unknown }>) => {
  storeManager.updateSettings(settings as Parameters<typeof storeManager.updateSettings>[0])
  return { success: true }
})

ipcMain.handle('translate', async (_, { text, targetLang }: { text: string, targetLang: string }) => {
  try {
    const response = await fetch('http://127.0.0.1:8000/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, target_lang: targetLang || 'zh-CN' })
    })
    const data = await response.json()
    return data
  } catch (error) {
    console.error('Translation error:', error)
    return { error: 'Translation service unavailable' }
  }
})

app.whenReady().then(() => {
  startPythonServer()
  createWindow()

  if (win) {
    new ViewManager(win)
  }
})
