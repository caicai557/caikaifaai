var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
import { ipcMain, BrowserView, app, BrowserWindow } from "electron";
import { createRequire } from "node:module";
import { fileURLToPath as fileURLToPath$1 } from "node:url";
import path$1 from "node:path";
import { spawn } from "node:child_process";
import path from "path";
import { fileURLToPath } from "url";
const __filename$1 = fileURLToPath(import.meta.url);
const __dirname$2 = path.dirname(__filename$1);
class ViewManager {
  constructor(window) {
    __publicField(this, "window");
    __publicField(this, "views", /* @__PURE__ */ new Map());
    __publicField(this, "currentViewId", null);
    // Preload path (adjust based on build structure)
    // In dev: src/preload/index.ts (but compiled to out/preload/index.js)
    // electron-vite defines __dirname for preload differently usually.
    __publicField(this, "preloadPath");
    this.window = window;
    this.preloadPath = path.join(__dirname$2, "preload.mjs");
    this.setupIPC();
  }
  setupIPC() {
    ipcMain.on("switch-view", (_, viewId) => {
      this.switchView(viewId);
    });
  }
  createView(id, url, userAgent) {
    if (this.views.has(id)) return;
    const view = new BrowserView({
      webPreferences: {
        preload: this.preloadPath,
        nodeIntegration: false,
        contextIsolation: true
      }
    });
    view.webContents.loadURL(url);
    if (userAgent) view.webContents.setUserAgent(userAgent);
    this.views.set(id, view);
  }
  switchView(id) {
    if (id === "home" || id === "settings" || id === "custom") {
      this.window.setBrowserView(null);
      this.currentViewId = null;
      return;
    }
    const view = this.views.get(id);
    if (!view) {
      if (id === "telegram") this.createView(id, "https://web.telegram.org/a/");
      if (id === "whatsapp") this.createView(id, "https://web.whatsapp.com/");
      if (id === "tiktok") this.createView(id, "https://www.tiktok.com/");
    }
    const targetView = this.views.get(id);
    if (targetView) {
      this.window.setBrowserView(targetView);
      const bounds = this.window.getBounds();
      targetView.setBounds({ x: 256, y: 0, width: bounds.width - 256, height: bounds.height });
      targetView.setAutoResize({ width: true, height: true });
      this.currentViewId = id;
    }
  }
}
app.disableHardwareAcceleration();
app.commandLine.appendSwitch("disable-gpu");
app.commandLine.appendSwitch("no-sandbox");
createRequire(import.meta.url);
const __dirname$1 = path$1.dirname(fileURLToPath$1(import.meta.url));
process.env.APP_ROOT = path$1.join(__dirname$1, "..");
const VITE_DEV_SERVER_URL = process.env["VITE_DEV_SERVER_URL"];
const MAIN_DIST = path$1.join(process.env.APP_ROOT, "dist-electron");
const RENDERER_DIST = path$1.join(process.env.APP_ROOT, "dist");
process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL ? path$1.join(process.env.APP_ROOT, "public") : RENDERER_DIST;
let win;
function createWindow() {
  win = new BrowserWindow({
    icon: path$1.join(process.env.VITE_PUBLIC, "electron-vite.svg"),
    webPreferences: {
      preload: path$1.join(__dirname$1, "preload.mjs")
    }
  });
  win.webContents.on("did-finish-load", () => {
    win == null ? void 0 : win.webContents.send("main-process-message", (/* @__PURE__ */ new Date()).toLocaleString());
  });
  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL);
  } else {
    win.loadFile(path$1.join(RENDERER_DIST, "index.html"));
  }
}
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
    win = null;
  }
});
app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
let pythonProcess = null;
function startPythonServer() {
  var _a, _b;
  const pythonExec = path$1.join(process.env.APP_ROOT, "../../.venv/bin/python");
  const scriptPath = path$1.join(process.env.APP_ROOT, "api/server.py");
  console.log("[Electron] Spawning Python Backend:", pythonExec, scriptPath);
  pythonProcess = spawn(pythonExec, [scriptPath], {
    env: { ...process.env, PORT: "8000", PYTHONUNBUFFERED: "1" },
    cwd: process.env.APP_ROOT
  });
  (_a = pythonProcess.stdout) == null ? void 0 : _a.on("data", (data) => {
    console.log(`[Python]: ${data.toString().trim()}`);
  });
  (_b = pythonProcess.stderr) == null ? void 0 : _b.on("data", (data) => {
    console.error(`[Python Err]: ${data.toString().trim()}`);
  });
  pythonProcess.on("error", (err) => {
    console.error("[Electron] Failed to start Python process:", err);
  });
  pythonProcess.on("exit", (code) => {
    console.log(`[Electron] Python process exited with code ${code}`);
  });
}
app.on("will-quit", () => {
  if (pythonProcess) {
    console.log("[Electron] Killing Python process...");
    pythonProcess.kill();
    pythonProcess = null;
  }
});
app.whenReady().then(() => {
  startPythonServer();
  createWindow();
  if (win) {
    new ViewManager(win);
  }
});
export {
  MAIN_DIST,
  RENDERER_DIST,
  VITE_DEV_SERVER_URL
};
