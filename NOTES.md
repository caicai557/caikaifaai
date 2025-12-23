# NOTES.md - 瞬态上下文记录

> [!TIP]
> 本文档用于记录会话中的关键决策、学到的经验、未完成的任务等信息。  
> 每次会话结束前，由 Gemini 总结本次会话的瞬态上下文并更新到此文件。

## 最后更新
**时间**: 2025-12-22 12:05  
**会话**: AGI 开发范式最佳实践实施

## 当前状态

### 已完成
- [x] 项目结构扫描
- [x] 审查 AGENTS.md 与 CLAUDE.md
- [x] 审查 MCP 配置
- [x] 增强 CLAUDE.md（添加 AGENTS.md 联动指令）
- [x] 创建 CODE_MAP.md
- [x] 创建 NOTES.md

### 进行中
- [ ] 第二阶段：理事会协同开发流命令创建

### 待办
- [ ] 创建 PRD 模板
- [ ] 创建架构审计命令
- [ ] 创建 TDD 测试命令
- [ ] 创建批量执行脚本
- [ ] 创建自愈校验命令
- [ ] 创建检查点总结命令
- [ ] 配置 Docker 沙箱
- [ ] 配置 Git Worktrees
- [ ] 端到端测试

## 关键决策

### 2025-12-22 - 认知对齐强化
- **决策**: 在 CLAUDE.md 顶部添加 IMPORTANT 警告框，强制引用 AGENTS.md
- **理由**: 建立"单一事实来源"，避免认知漂移
- **影响**: 所有智能体在执行任务前必须先遵守 AGENTS.md 规则

### 2025-12-22 - 代码地图创建
- **决策**: 创建 CODE_MAP.md 作为项目全局导航
- **理由**: 让智能体无需读取万行代码即可理解项目结构
- **内容**: 目录结构、核心配置、MCP 工具、工作流模式、安全边界

## 学到的经验

1. **文件联动**: 通过 markdown 链接和 IMPORTANT 警告框，可以建立文档间的强制依赖关系
2. **权限分层**: .claude/settings.json 的 deny/allow/ask 三级权限模型非常有效
3. **MCP 集成**: 已配置 filesystem、codex、gemini 三个 MCP 服务器

## 技术债务

- [ ] Docker Compose 配置未创建（环境隔离）
- [ ] Git Worktrees 脚本未编写（并行开发）
- [ ] 自愈循环未实现（Self-Healing Loop）
- [ ] Wald 共识算法未集成（智能体决策）

## 下次会话重点

1. 创建第二阶段的六个命令模板
2. 编写批量执行脚本（tools/batch_executor.py）
3. 测试完整工作流
4. 创建 walkthrough.md

## 参考资源

- [AGENTS.md](file:///home/dabah123/projects/caicai/AGENTS.md): 治理规则
- [CLAUDE.md](file:///home/dabah123/projects/caicai/CLAUDE.md): 工作流契约
- [CODE_MAP.md](file:///home/dabah123/projects/caicai/CODE_MAP.md): 项目导航
- [.mcp.json](file:///home/dabah123/projects/caicai/.mcp.json): MCP 配置
