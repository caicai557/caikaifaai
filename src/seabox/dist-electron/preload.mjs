"use strict";
var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
const electron = require("electron");
const getIPC = () => {
  return window.ipcRenderer || null;
};
const CONFIG = {
  targetLang: "zh-CN"
};
const STYLES = `
  :host {
    display: block;
    margin-top: 6px;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  }
    .apple-overlay {
    padding: 10px 14px;
    border-radius: 12px;
    background: rgba(250, 250, 252, 0.85);
    backdrop-filter: blur(25px) saturate(180%);
    -webkit-backdrop-filter: blur(25px) saturate(180%);
    border: 0.5px solid rgba(0, 0, 0, 0.1);
    box-shadow: 
      0 4px 6px -1px rgba(0, 0, 0, 0.05), 
      0 10px 24px -4px rgba(0, 0, 0, 0.12);
    animation: popIn 0.35s cubic-bezier(0.25, 0.1, 0.25, 1.0) forwards;
    transform-origin: top left;
  }
  @media (prefers-color-scheme: dark) {
    .apple-overlay {
      background: rgba(35, 35, 35, 0.85);
      border-color: rgba(255, 255, 255, 0.12);
      color: #FFFFFF;
      box-shadow: 
        0 4px 6px -1px rgba(0, 0, 0, 0.2), 
        0 10px 24px -4px rgba(0, 0, 0, 0.3);
    }
  }
  .header {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 4px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #8E8E93;
  }
  .content {
    font-size: 13px;
    line-height: 1.4;
    color: #1C1C1E;
    white-space: pre-wrap;
  }
  @media (prefers-color-scheme: dark) {
    .content { color: #FFFFFF; }
  }
  @keyframes popIn {
    from { opacity: 0; transform: translateY(4px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
  .loading {
    height: 12px;
    width: 60%;
    background: linear-gradient(90deg, rgba(150,150,150,0.1), rgba(150,150,150,0.2), rgba(150,150,150,0.1));
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
  }
  @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
`;
class SeaBoxOverlay extends HTMLElement {
  constructor() {
    super();
    __publicField(this, "root");
    __publicField(this, "contentDiv");
    this.root = this.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = STYLES;
    this.root.appendChild(style);
    const wrapper = document.createElement("div");
    wrapper.className = "apple-overlay";
    const header = document.createElement("div");
    header.className = "header";
    header.innerHTML = "<span>🌐</span> SEABOX TRANSLATE";
    this.contentDiv = document.createElement("div");
    this.contentDiv.className = "content";
    this.contentDiv.innerHTML = '<div class="loading"></div>';
    wrapper.appendChild(header);
    wrapper.appendChild(this.contentDiv);
    this.root.appendChild(wrapper);
  }
  updateContent(text) {
    this.contentDiv.textContent = text;
  }
}
function registerSeaBoxOverlay() {
  if (typeof customElements !== "undefined" && customElements && !customElements.get("seabox-overlay")) {
    customElements.define("seabox-overlay", SeaBoxOverlay);
  }
}
const cache = /* @__PURE__ */ new Map();
async function translateText(text, overrideTargetLang) {
  const targetLang = CONFIG.targetLang;
  if (!text || text.length < 2) return null;
  const cacheKey = `${text}:${targetLang}`;
  if (cache.has(cacheKey)) return cache.get(cacheKey);
  try {
    const ipc = getIPC();
    if (!ipc) return null;
    const result = await ipc.invoke("translate", { text, targetLang });
    if (result && result.translated) {
      cache.set(cacheKey, result.translated);
      return result.translated;
    }
  } catch (e) {
    console.error("[SeaBox] Translation fail:", e);
  }
  return null;
}
async function processMessage(element) {
  if (element.querySelector("seabox-overlay")) return;
  const textNode = element.querySelector(".text-content") || element;
  const text = (textNode.textContent || "").trim();
  if (!text || text.length < 2 || /^\d+:\d+$/.test(text)) return;
  const overlay = new SeaBoxOverlay();
  element.appendChild(overlay);
  const translated = await translateText(text);
  if (translated && translated !== text) {
    overlay.updateContent(translated);
  } else {
    overlay.remove();
  }
}
function initTelegramGovernance() {
  console.log("[SeaBox] Governance Module Loaded");
  registerSeaBoxOverlay();
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((m) => {
      m.addedNodes.forEach((node) => {
        if (node instanceof HTMLElement) {
          if (node.matches('.message, .bubble, [class*="message"]')) {
            processMessage(node);
          } else {
            const msgs = node.querySelectorAll('.message, .bubble, [class*="message"]');
            msgs.forEach(processMessage);
          }
        }
      });
    });
  });
  const start = () => {
    const container = document.querySelector(".messages-container, .bubbles, .bubbles-group, #MiddleColumn");
    if (container) {
      observer.observe(container, { childList: true, subtree: true });
      console.log("[SeaBox] Observer Started on", container);
      document.querySelectorAll(".message, .bubble").forEach(processMessage);
    } else {
      setTimeout(start, 2e3);
    }
  };
  start();
  initOutgoingGovernance();
}
let previewOverlay = null;
let currentTranslation = "";
let isBlocked = false;
let inputDebounceTimer;
function showPreview(inputElement, text, blocked = false) {
  if (!previewOverlay) {
    previewOverlay = document.createElement("div");
    previewOverlay.className = "apple-overlay";
    previewOverlay.style.position = "absolute";
    previewOverlay.style.zIndex = "9999";
    document.body.appendChild(previewOverlay);
  }
  const rect = inputElement.getBoundingClientRect();
  previewOverlay.style.left = `${rect.left}px`;
  previewOverlay.style.bottom = `${window.innerHeight - rect.top + 10}px`;
  previewOverlay.innerHTML = `<div class="header">${blocked ? "⛔ BLOCKED" : "📤 PREVIEW (EN)"}</div><div class="content" style="${blocked ? "color: red;" : ""}">${text}</div>${blocked ? '<div style="font-size:10px;color:#888;">翻译不完整，无法发送</div>' : ""}`;
}
function handleInput(e) {
  const target = e.target;
  if (!target.isContentEditable && target.tagName !== "TEXTAREA" && target.tagName !== "INPUT") return;
  const text = (target.textContent || target.value || "").trim();
  if (inputDebounceTimer) clearTimeout(inputDebounceTimer);
  if (!text || !/[\u4e00-\u9fa5]/.test(text)) {
    if (previewOverlay) previewOverlay.remove();
    previewOverlay = null;
    currentTranslation = "";
    return;
  }
  inputDebounceTimer = setTimeout(async () => {
    const ipc = getIPC();
    if (!ipc) return;
    const result = await ipc.invoke("translate", { text, targetLang: "en" });
    if (result && result.translated) {
      currentTranslation = result.translated;
      isBlocked = result.blocked || false;
      showPreview(target, result.translated, isBlocked);
    }
  }, 300);
}
function handleKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey && currentTranslation && previewOverlay) {
    if (isBlocked) {
      e.preventDefault();
      e.stopPropagation();
      alert("翻译不完整，无法发送。请修改内容后重试。");
      return;
    }
    e.preventDefault();
    e.stopPropagation();
    const target = e.target;
    if (target.isContentEditable) {
      target.textContent = currentTranslation;
    } else if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) {
      target.value = currentTranslation;
    }
    target.dispatchEvent(new Event("input", { bubbles: true }));
    previewOverlay.remove();
    previewOverlay = null;
    currentTranslation = "";
    isBlocked = false;
  }
}
function initOutgoingGovernance() {
  document.addEventListener("input", handleInput, true);
  document.addEventListener("keydown", handleKeydown, true);
  console.log("[SeaBox] Outgoing Governance Ready");
}
electron.contextBridge.exposeInMainWorld("ipcRenderer", {
  on(...args) {
    const [channel, listener] = args;
    return electron.ipcRenderer.on(channel, (event, ...args2) => listener(event, ...args2));
  },
  off(...args) {
    const [channel, ...omit] = args;
    return electron.ipcRenderer.off(channel, ...omit);
  },
  send(...args) {
    const [channel, ...omit] = args;
    return electron.ipcRenderer.send(channel, ...omit);
  },
  invoke(...args) {
    const [channel, ...omit] = args;
    return electron.ipcRenderer.invoke(channel, ...omit);
  }
  // You can expose other APIs you need here.
  // ...
});
window.addEventListener("DOMContentLoaded", () => {
  const host = window.location.hostname;
  if (host.includes("telegram") || host.includes("web.telegram.org")) {
    console.log("[SeaBox] Telegram Detected - Governance Active");
    initTelegramGovernance();
  }
});
