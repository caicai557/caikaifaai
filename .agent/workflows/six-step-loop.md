---
description: "完整的六步自愈循环开发工作流"
---

# 六步自愈循环工作流

完整的 AGI 开发范式工作流，从需求到交付的自动化流程。

## 前置条件

- [x] 已阅读 [AGENTS.md](file:///home/dabah123/projects/caicai/AGENTS.md)
- [x] 已阅读 [CLAUDE.md](file:///home/dabah123/projects/caicai/CLAUDE.md)
- [x] Docker 沙箱已启动: `docker-compose up -d`
- [x] Git 仓库状态干净: `git status`

## 工作流步骤

### Step 1: 需求代码化 (PM 阶段)
**主控者**: Codex  
**命令**: `/prd_generate "<功能描述>"`

```bash
# 示例
/prd_generate "实现用户登录功能，支持邮箱+密码认证"
```

**输出**: `prd_output.yaml`  
**验证**: 
```bash
yq '.prd.title' prd_output.yaml
yq '.task_tree[].name' prd_output.yaml
```

---

### Step 2: 全库审计与方案设计 (架构师阶段)
**主控者**: Gemini Pro  
**命令**: `/audit_design "<架构审计目标>"`

```bash
# 示例
/audit_design "用户登录功能的架构设计和冲突扫描"
```

**输出**: `audit_output.yaml`  
**验证**:
```bash
yq '.audit_report.conflicts | length' audit_output.yaml
yq '.audit_report.technical_design.file_structure' audit_output.yaml
```

**审查重点**: 
- 是否有 blocker 级别冲突
- 设计决策的 rationale 是否合理
- 安全考虑是否充分

---

### Step 3: TDD 强制约束 (QA 阶段)
**主控者**: Claude Code  
**命令**: `/tdd_tests "<测试目标>"`

```bash
# 示例
/tdd_tests "为用户登录功能生成完整测试套件"
```

**输出**: `tests.json`  
**阻断条件**: 
```bash
# 测试覆盖率必须 ≥ 90%
npm test -- --coverage
# 如果 < 90%，禁止进入 Step 4
```

**验证**:
```bash
npm test -- --listTests
npm test -- --coverage --verbose
```

---

### Step 4: 程序化并行执行 (执行官阶段)
**主控者**: Claude Code  
**工具**: `batch_executor.py`

#### 4.1 创建执行计划
```yaml
# execution_plan.yaml
tasks:
  - name: "创建 JWT 服务"
    type: file_write
    path: src/auth/jwt-service.ts
    content: |
      export class JWTService { ... }
    critical: true

  - name: "运行测试"
    type: command
    cmd: npm test
    critical: true
```

#### 4.2 在沙箱中执行
// turbo
```bash
docker-compose exec python-sandbox python /workspace/tools/batch_executor.py /workspace/execution_plan.yaml
```

**Token 节省**: 相比自然语言指令节省 ~98.7%

---

### Step 5: 自愈校验与 Wald 共识 (裁决阶段)
**主控者**: Claude Code  
**命令**: `/self_heal`

```bash
/self_heal
```

**自愈循环**:
1. 运行测试
2. 如果失败 → 分析错误 → 自动修复或生成补丁
3. 重新运行测试
4. 最多 5 次迭代

**Wald 共识**:
- 如果 π ≥ 0.95 → 自动提交
- 如果 π ≤ 0.30 → 拒绝并回滚
- 否则 → 申请人工审计

**输出**: `self_healing_report.yaml`

---

### Step 6: 完成总结与检查点 (记录员阶段)
**主控者**: Claude Code + Gemini Pro  
**命令**: `/checkpoint "<任务标签>"`

```bash
# 示例
/checkpoint "用户登录功能完成"
```

**自动执行**:
1. 创建 Git 提交
2. 运行最终验证
3. 调用 Gemini 生成总结
4. 更新 NOTES.md
5. 记录检查点到 `.last_checkpoint`

**输出**: `checkpoint.yaml`

---

## 完整示例

```bash
# 启动沙箱
docker-compose up -d

# Step 1: 需求
/prd_generate "用户登录功能(JWT认证)"

# Step 2: 设计
/audit_design "登录功能架构审计"

# Step 3: 测试
/tdd_tests "生成登录测试套件"

# 验证覆盖率
docker-compose exec nodejs-sandbox pnpm test -- --coverage
# 必须 ≥ 90% 才能继续

# Step 4: 执行
docker-compose exec python-sandbox python /workspace/tools/batch_executor.py /workspace/execution_plan.yaml

# Step 5: 自愈
/self_heal

# Step 6: 检查点
/checkpoint "登录功能完成"

# 清理会话 (可选)
/clear
```

## 并行开发 (Git Worktrees)

```bash
# 创建功能分支的 worktree
./tools/worktree.sh create feature-login

# 创建 bugfix 的 worktree
./tools/worktree.sh create bugfix-auth

# 在不同的 Claude Code 窗口中打开各自的 worktree
# 窗口 1: cd ../worktrees/feature-login
# 窗口 2: cd ../worktrees/bugfix-auth

# 各自独立运行六步流程，互不干扰
```

## 故障处理

### 测试覆盖率不达标
```bash
# 补充测试
/tdd_tests "补充边界条件测试"

# 重新验证
npm test -- --coverage
```

### 自愈失败 (超过 5 次迭代)
```bash
# 查看详细报告
cat self_healing_report.yaml

# 手动修复
# ... 修复代码 ...

# 重新自愈
/self_heal
```

### 需要回滚
```bash
# 回滚到上一个检查点
git reset --hard $(cat .last_checkpoint)

# 或使用 Claude Code
/rewind
```

## 最佳实践

1. **Small Diffs**: 每次改动 ≤ 200 行
2. **TDD 优先**: 先写测试，覆盖率 ≥ 90%
3. **沙箱隔离**: 所有执行在 Docker 中
4. **频繁检查点**: 每个功能完成后立即 checkpoint
5. **并行加速**: 使用 worktrees 多任务并行

## 工具链总览

```mermaid
graph LR
    A[/prd_generate] --> B[/audit_design]
    B --> C[/tdd_tests]
    C --> D{覆盖率≥90%?}
    D -->|No| C
    D -->|Yes| E[batch_executor.py]
    E --> F[/self_heal]
    F --> G{测试通过?}
    G -->|No| H{迭代<5?}
    H -->|Yes| E
    H -->|No| I[人工介入]
    G -->|Yes| J{Wald π≥0.95?}
    J -->|Yes| K[/checkpoint]
    J -->|No| I
    K --> L[完成]
```
