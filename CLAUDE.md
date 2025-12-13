# \# 项目：E:\\caicai（Electron | Multi-BrowserView | Telegram Web-A 多开隔离 + 自动翻译 + 客服线性流程自动回复）

# 

# 本文件用于指导 Claude Code 在此仓库内工作时的行为边界、工程闸门与常用命令。

# 

# ---

# 

# \## 项目说明

# 

# 用途：

# \- 收到消息 → 自动翻译 → 在“线性客服流程（状态机）”中做节点判定 → 从固定话术库选择模板回复（仅变量填充）

# 

# 强调：

# \- 多开隔离：多账号并行，cookie/session/缓存/日志/状态必须隔离

# \- 稳定性优先：异常重连、幂等去重、乱序与重入控制必须先于功能扩展

# 

# ---

# 

# \## 技术栈（TBD 用 /onboard 自动识别补齐）

# \- Node.js: TBD

# \- Electron: TBD（主进程 + 多 BrowserView）

# \- 前端框架/构建工具：TBD（Vue/React/Vite 等）

# \- 翻译：Google 翻译（建议优先使用 Google Cloud Translation API；若使用网页翻译，必须承认不稳定并加更强兜底）

# 

# ---

# 

# \## 常用开发命令（按你的项目脚本改成真实存在的）

# ```bash

# npm install

# npm run dev

# npm run lint

# npm run typecheck

# npm test

# npm run build



核心架构（建议按“管理器模式”对标）
===

# 

# 主进程建议采用管理器模式（目录可对标参考结构）：

# 

# WindowManager：窗口管理

# 

# ViewManager：BrowserView 生命周期管理（创建/销毁/挂载/切换）

# 

# AccountManager：账号/实例管理（instanceId、accountId、启动/停止）

# 

# SessionManager：隔离分区（partition/persist）与目录策略

# 

# FlowManager：线性流程状态机（节点表驱动）

# 

# TranslationManager：翻译调用（缓存/限流/失败策略）

# 

# DedupeManager：幂等去重（dedupeKey、TTL）

# 

# ReconnectManager：异常重连（退避/抖动/熔断）

# 

# TelemetryManager：日志与指标（统一字段）

# 

# 多开隔离（必须遵守的硬约束）

# 

# 每个账号实例必须使用独立 session partition：

# 

# 推荐：persist:acc\_<accountId>

# 

# 禁止：多个账号共用 default session 或共用同一 partition

# 

# 每个账号实例必须隔离：

# 

# 浏览器存储（cookie/localStorage/indexedDB）

# 

# 缓存/下载/临时目录

# 

# 日志文件（按 accountId/instanceId 分桶）

# 

# IPC 路由必须携带 accountId/instanceId，禁止“全局单例状态”导致串线

# 

# 翻译子系统（必须实现）

# 

# 必须：超时、重试、限流、缓存（同一句话重复出现必须命中缓存）

# 

# 必须：失败策略（翻译失败时进入 fallback/提示人工接管/原文直通的明确选择）

# 

# 禁止：翻译失败时“猜测语义”或编造内容

# 

# 建议：翻译结果用于匹配（matchOn=translatedText），原文保留用于审计/定位（脱敏/截断）

# 

# 可靠性（必须实现）

# 幂等/去重（必须）

# 

# 同一 message 在同一 chat 中最多处理一次

# 

# dedupeKey：accountId + chatId + messageId

# 

# messageId 缺失时兜底：hash(text + senderId + ts)

# 

# 必须记录：dedupeKey、是否命中、命中原因、TTL

# 

# 异常重连（必须）

# 

# 网络错误/页面崩溃/注入失效：必须自动恢复

# 

# 重连策略：指数退避 + 抖动；最大重试；熔断冷却

# 

# 恢复后严格去重，避免重复回复

# 

# 乱序与重入（必须）

# 

# 同一 chatId 的状态更新必须串行（队列/锁）

# 

# 未匹配输入必须走 fallback（不允许卡死）

# 

# 可观测性（必须）

# 

# 最小日志字段：

# 

# ts, accountId, instanceId, chatId, messageId, nodeId, event, reason, latencyMs, retryCount

# 敏感信息处理：

# 

# 禁止记录验证码/密码/token/隐私内容（必须脱敏/截断）

# 

# 全局开关：

# 

# 全局停机、账号级停机、会话级停机（人工接管）

# 

# 工程闸门（每次改动必须过）

# 

# /spec：输出可测验收（含失败兜底）

# 

# /flow：输出状态机 JSON（含 fallback、翻译/去重/重连策略）

# 

# /step：先计划后改文件（一次一件事）

# 

# /test：产出可复现证据（命令或手动回归脚本）

# 

# /review\_gate：必审 幂等/重连/乱序/隔离边界

# 

# /pr：必须包含回滚步骤与监控点

# 

# 合规边界（必须遵守）

# 

# 不做批量骚扰、群发营销、刷量

# 

# 不做绕平台风控、隐匿自动化痕迹、对抗检测

# 

# 本项目定位为“自有账号/自有业务”的客服自动化与效率工具

