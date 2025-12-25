# SeaBox 开发进展 - 2025年12月25日

## 已完成任务

### 侧边栏重构与 Telegram 聚焦
- [x] **UI 风格重塑**：实现了卡片式布局、高保真图标背景和 Apple 风格的阴影反馈。
- [x] **多实例支持**：添加了“添加新窗口”按钮，支持动态增加 Telegram 实例。
- [x] **BrowserView 适配**：重构了视图加载逻辑，确保 React 渲染层不遮挡原生网页视图。

### 侧边栏宽度自由调节 (2025 最佳实践)
- [x] **动态同步架构**：实现了 React 状态 -> IPC -> Main Process -> BrowserView Bounds 的实时同步。
- [x] **交互增强**：
    - 添加了 4px 的可见拖拽热区。
    - 实现了拖拽期间的全局事件遮罩，防止 iframe/webview 拦截鼠标。
    - 优化了窄宽度下的文字自动截断（Truncate）。
- [x] **性能优化**：通过主进程监听窗口 resize 事件，确保在任何情况下视图对齐。

### 侧边栏内容自适应 (Container Queries)
- [x] **技术选型**：引入 `tailwindcss/container-queries` 实现组件级响应式。
- [x] **三级断点策略**：
    - 窄模式 (<300px)：紧凑布局。
    - 标准模式 (300px+)：优化阅读体验。
    - 宽模式 (400px+)：大尺寸沉浸式展示。
- [x] **全元素动效**：图标、文字、间距均实现了流体过渡动画。

## 后续计划
- [x] ~~实现侧边栏宽度的持久化存储~~（已完成）
- [x] ~~增强 Telegram 多实例的隔离性（Session 分离）~~（已完成）
- [x] 集成 AI 翻译与治理插件（sidecar 逻辑对接）

### 状态持久化 (electron-store)
- [x] **技术选型**：采用 `electron-store` 实现跨进程、容错的本地存储。
- [x] **StoreManager 模块**：封装了侧边栏宽度、Telegram 实例列表、窗口状态的读写 API。
- [x] **IPC 桥接**：通过 `get-settings` / `set-settings` 实现渲染进程与主进程的状态同步。
- [x] **自动恢复**：
    - 窗口位置/大小：关闭应用后重启自动恢复。
    - 侧边栏宽度：拖动后自动保存，重启后自动恢复。
    - Telegram 实例：添加的实例在重启后保留。

### 侧边栏优化
- [x] **极窄模式**：最小宽度调整为 80px（原 240px）。
- [x] **自适应布局**：使用 Container Queries 实现：
    - < 150px：纯图标模式（自动隐藏文字，居中图标）
    - > 150px：标准图文模式
- [x] **平滑过渡**：宽度变化时元素布局平滑切换。

- [x] **视觉优化**：
    - Telegram 图标替换为官方 SVG。
    - 极窄模式下图标尺寸缩小（w-8），视觉更精致。
    - 底部设置按钮样式优化，极窄模式下自动变为圆形居中。

### Session 隔离 (多账号支持)
- [x] **技术实现**：使用 `session.fromPartition('persist:xxx')` 为每个 Telegram 窗口创建独立 Session。
- [x] **数据隔离**：每个窗口拥有独立的 Cookies、localStorage、缓存。
- [x] **持久化登录**：登录状态跨应用重启保留。
- [x] **ViewManager 升级**：根据 StoreManager 中的 partition 字段动态创建隔离视图。

### 双向翻译与治理 (2025 Best Practices)
- [x] **Sidecar 架构**：实现 Electron IPC -> Python FastAPI 的高效治理通道。
- [x] **双向翻译**：
    - **接收端**：Telegram 消息自动翻译，使用 Shadow DOM 技术注入无感悬浮窗 (Apple 风格)。
    - **发送端**：拦截输入事件，实时预览英文，回车自动替换发送 (Type Chinese, Send English)。
- [x] **隐私治理 (Level 1)**：在 Python 端集成了 PII 脱敏中间件，自动过滤邮箱、电话和加密货币地址。
- [x] **翻译质量检测**：发送英文时，若翻译结果仍含中文，自动拦截并提示用户修改。

### 右键菜单功能 (Context Menu)
- [x] **ContextMenu 组件**：创建 Apple 风格的右键菜单组件，支持 5 种操作。
- [x] **刷新 (Refresh)**：调用 `webContents.reload()` 刷新 Telegram 页面。
- [x] **休眠 (Hibernate)**：销毁 BrowserView 释放内存，保留 Session 数据。
- [x] **删除 (Delete)**：从配置中移除实例，带确认弹窗。
- [x] **置顶 (Pin)**：添加 `isPinned` 字段，支持优先显示。
### UI/UX 升级 (Apple Design)
- [x] **Mica 材质**：重构 Sidebar 背景为半透明模糊效果，模拟 macOS Mica。
- [x] **iPadOS 导航**：采用全宽 Selection Pill，优化点击和悬停态。
- [x] **微交互 (Micro-interactions)**：添加 `active:scale` 按压反馈和 `apple-ease` 缓动曲线。
### 视觉优化 (Visual Polish)
- [x] **无边框设计**：移除侧边栏右侧分割线，仅用光影区分。
- [x] **Overlay Scrollbar**：实现类似 macOS 的隐藏式滚动条，悬停可见，无轨道背景。
- [x] **居中布局**：修复极窄模式下图标未居中的问题。
- [x] **高对比度字体**：提升未选中状态文字的对比度和字号。
- [x] **交互微调**：修复设置按钮的缩放动画，移除无效的滚动样式。
- [x] **Window Controls**：移动红绿灯至右侧，并调整尺寸为 14px，优化点击区域。

### Bug 修复 (2025-12-25)
- [x] **右键菜单修复**：修复侧边栏右键菜单功能无响应问题。
    - 问题原因：`TelegramInstance` 接口缺少 `isPinned`/`isHibernated` 属性。
    - 解决方案：在 `App.tsx` 和 `Sidebar.tsx` 中补全接口定义，并确保 `menuItems` 正确传递这些属性。
- [x] **Session 持久化确认**：Telegram 账号缓存使用 `persist:` 前缀的 partition，登录状态可跨重启保留。
- [x] **Telegram 白屏修复**：`telegram-governance.ts` 错误直接导入 `electron.ipcRenderer`，在 contextIsolation=true 时失败。已改用 preload 暴露的 `getIPC()` 辅助函数。
- [x] **EIO 错误修复**：添加 `safeLog`/`safeError` 函数包装 console 输出，防止写入错误导致崩溃。
