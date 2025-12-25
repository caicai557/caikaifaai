import { app, BrowserWindow } from 'electron'

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
  win = new BrowserWindow({
    icon: path.join(process.env.VITE_PUBLIC, 'electron-vite.svg'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.mjs'),
    },
  })

  // Test active push message to Renderer-process.
  win.webContents.on('did-finish-load', () => {
    win?.webContents.send('main-process-message', (new Date).toLocaleString())
  })

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL)
  } else {
    // win.loadFile('dist/index.html')
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

app.whenReady().then(() => {
  startPythonServer()
  createWindow()

  if (win) {
    new ViewManager(win)
  }
})
