---
description: "检查点: 建立快照,总结上下文,支持回滚"
---

# 检查点总结命令

## 用途
任务结束后，建立 Git 快照，由 Gemini 总结本次会话的"瞬态上下文"并更新至 NOTES.md，支持 /rewind 回滚和 /clear 会话重置。

## 主控者
**Claude Code** - 编排引擎  
**Gemini Pro** - 总结引擎

## 执行方式
```bash
/checkpoint "任务描述或标签"
```

## 输出格式 (YAML)

```yaml
checkpoint:
  id: "ckpt_20251222_120000"
  timestamp: "2025-12-22T12:00:00Z"
  task: "实现用户登录功能"
  
  git_snapshot:
    branch: "feature/user-login"
    commit_sha: "b7d4e1a"
    commit_message: |
      feat: 实现用户登录功能
      
      - 添加 JWT 认证服务
      - 实现密码哈希
      - 添加速率限制中间件
      - 测试覆盖率: 92.3%
    
    files_changed:
      added:
        - src/auth/jwt-service.ts
        - src/auth/password-hasher.ts
        - src/middleware/rate-limiter.ts
        - src/auth/jwt-service.test.ts
      modified:
        - src/api/routes.ts
        - package.json
      deleted: []
    
    stats:
      total_lines_added: 387
      total_lines_deleted: 12
      files_changed: 5
  
  test_status:
    command: "npm test -- --coverage"
    passed: true
    coverage:
      statements: 92.3
      branches: 88.7
      functions: 94.1
      lines: 91.8
    test_count:
      total: 48
      passed: 48
      failed: 0
  
  context_summary:
    generated_by: "Gemini Pro"
    
    what_was_built:
      - "JWT 认证服务，支持 token 生成和验证"
      - "密码哈希服务，使用 bcrypt (成本因子 12)"
      - "速率限制中间件，防止暴力破解 (10次/小时)"
      - "完整的单元测试和集成测试套件"
    
    key_decisions:
      - decision: "使用 JWT 而非 Session"
        rationale: "无状态设计，便于横向扩展"
        
      - decision: "速率限制设为 10次/小时/IP"
        rationale: "平衡安全性与用户体验"
        
      - decision: "bcrypt 成本因子设为 12"
        rationale: "安全性与性能的权衡 (~200ms/hash)"
    
    challenges_encountered:
      - challenge: "JWT 过期检查逻辑缺失"
        solution: "自愈循环自动添加过期时间验证"
        
      - challenge: "速率限制初始设计遗漏"
        solution: "架构审计发现，调用 /codex_patch_plan 补充"
    
    learned_lessons:
      - "TDD 强制约束有效防止了大量返工"
      - "架构审计的长上下文扫描发现了 3 处潜在冲突"
      - "自愈循环节省了约 40% 的手动修复时间"
    
    technical_debt:
      - "JWT 刷新 token 机制未实现"
      - "速率限制暂未持久化，重启后重置"
      - "缺少登录审计日志"
    
    next_steps:
      - "实现 JWT 刷新机制"
      - "添加 Redis 支持速率限制持久化"
      - "集成审计日志系统"
  
  notes_update:
    file: "NOTES.md"
    action: "append"
    content: |
      ## 2025-12-22 12:00 - 用户登录功能
      
      ### 已完成
      - JWT 认证服务 (src/auth/jwt-service.ts)
      - 密码哈希 (bcrypt, 成本因子 12)
      - 速率限制中间件 (10次/小时)
      - 测试覆盖率: 92.3%
      
      ### 关键决策
      - JWT vs Session: 选择 JWT (无状态扩展)
      - 速率限制: 10次/小时/IP
      
      ### 技术债务
      - [ ] JWT 刷新机制
      - [ ] 速率限制持久化 (Redis)
      - [ ] 审计日志
  
  rewind_support:
    enabled: true
    command: "git reset --hard b7d4e1a"
    safe_to_rewind: true
    uncommitted_changes: false
  
  session_management:
    current_session_id: "sess_abc123"
    total_tokens_used: 45000
    total_tool_calls: 78
    duration_minutes: 35
    
    should_clear: false
    clear_reason: null
    
    next_session_recommendations:
      - "会话 token 使用正常，可继续"
      - "如需开始新任务，建议调用 /clear 重置"

verification:
  - cmd: "git log -1 --oneline"
    expected: "显示最新提交"
  
  - cmd: "git status"
    expected: "working tree clean"
  
  - cmd: "npm test -- --coverage --silent"
    expected: "所有测试通过"
  
  - cmd: "tail -20 NOTES.md"
    expected: "显示最新的上下文更新"
```

## 工作流程

### 1. 创建 Git 快照
```bash
# 自动执行
git add .
git commit -m "feat: <任务描述>"
git log -1 --pretty=format:"%H" > .last_checkpoint
```

### 2. 运行最终验证
```bash
npm test -- --coverage
npm run lint
npm run build  # 如果适用
```

### 3. 调用 Gemini 生成总结
```bash
gpp "Summarize the context of this task: <task_description>. 
Review git diff, test results, and generate a concise summary."
```

### 4. 更新 NOTES.md
```bash
# 追加到 NOTES.md
echo "\n## $(date) - <task>" >> NOTES.md
echo "<summary_from_gemini>" >> NOTES.md
```

### 5. 会话清理（可选）
```bash
# 如果会话很长或任务已完成，建议重置
# Claude Code 会话命令: /clear
```

## 使用示例

### 完整六步流程
```bash
# Step 1: 需求代码化 (PM)
/prd_generate "用户登录功能"

# Step 2: 全库审计 (架构师)
/audit_design "登录功能架构"

# Step 3: TDD 强制 (QA)
/tdd_tests "生成登录测试"

# Step 4: 程序化执行 (执行官)
python tools/batch_executor.py execution_plan.yaml

# Step 5: 自愈校验 (裁决)
/self_heal

# Step 6: 检查点总结 (记录员)
/checkpoint "用户登录功能完成"
```

### 检查点回滚
```bash
# 查看检查点
git log --oneline

# 回滚到上一个检查点
git reset --hard $(cat .last_checkpoint)

# 或使用 Claude Code 的 /rewind 命令
/rewind
```

## 快照策略

### 何时创建检查点
- ✅ 完成一个完整的功能模块
- ✅ 所有测试通过且覆盖率达标
- ✅ 代码已通过 lint 和 build
- ✅ 自愈循环成功收敛

### 何时跳过检查点
- ❌ 测试未通过
- ❌ 有未解决的冲突
- ❌ 覆盖率 < 90%
- ❌ 仍在调试中

## NOTES.md 格式规范

```markdown
# NOTES.md

## 2025-12-22 12:00 - 用户登录功能
### 已完成
- 功能1
- 功能2

### 关键决策
- 决策: 理由

### 技术债务
- [ ] 待办1
- [ ] 待办2

### 下次重点
- 重点1
```

## 会话管理策略

### 何时调用 /clear
- Token 使用 > 80% (超过 160k/200k)
- 工具调用 > 100 次
- 会话时长 > 60 分钟
- 任务完全完成，开始新任务

### /clear 前必做
1. ✅ 调用 /checkpoint 保存状态
2. ✅ 确认 git commit 已提交
3. ✅ 确认 NOTES.md 已更新
4. ✅ 无未完成的关键任务

## 检查点验证清单

- [ ] Git 快照已创建
- [ ] 提交信息清晰描述变更
- [ ] 所有测试通过
- [ ] 代码覆盖率 ≥ 90%
- [ ] NOTES.md 已更新
- [ ] 技术债务已记录
- [ ] .last_checkpoint 已更新

## 下游工作

- 检查点创建后 → 可安全 /clear 重置会话
- 发现问题 → /rewind 回滚到检查点
- 新任务开始 → 从 NOTES.md 恢复上下文
