# 2025 AGI 编排与决策层最佳实践

> **来源**: 2025.12.26 最新 AGI 开发范式
> **标签**: `orchestration`, `decision`, `wald`, `consensus`, `hitl`, `codification`

---

## 1. 模型选型与角色架构

### 编排者选型

- **优先使用强推理模型**: Codex 5.2 (o1/GPT-5.2) 或 o3-mini
- 能自主推断任务参数、环境约束
- 独立完成复杂任务拆解，无需过度人工指令

### 层级化监督模式 (Hierarchical Supervision)

```
┌─────────────────────────────────────────────┐
│           理事会主席 (Orchestrator)           │
│           - 对接用户                          │
│           - 拆解需求                          │
│           - 分发子任务                        │
└────────────────┬────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐
│WebSurfer│  │ Coder  │  │Auditor │
│(工具权限)│  │(工具权限)│  │(只读)  │
└────────┘  └────────┘  └────────┘
```

---

## 2. 基于"双账本"的状态管理

### Task Ledger (任务账本)

- **已知事实**: 确认的信息
- **待查信息**: 需要查询的问题
- **待推导结论**: 需要推理的结果
- **初始执行计划**: 预填"经验猜测"

### Progress Ledger (进度账本)

每轮迭代自我反思 **5 个核心问题**:

1. 任务是否完成？
2. 是否存在死循环？
3. 进度是否停滞？
4. 下一位发言者是谁？
5. 具体的执行指令是什么？

### 停滞计数器

```python
stagnation_count = 0
MAX_STAGNATION = 3

if no_progress:
    stagnation_count += 1
    if stagnation_count >= MAX_STAGNATION:
        trigger_replanning()  # 强制重规划
        stagnation_count = 0
```

---

## 3. 科学的共识构建与动态终止逻辑

### Wald 序列分析算法 (SPRT)

```
WaldConsensusDetector 实时评估 π (共识概率)

┌─────────────────────────────────────────────┐
│                                             │
│   π ≥ α (置信上限)                          │
│   → 立即终止辩论，输出最终决定              │
│   → 避免无效 Token 浪费                     │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│   π ≤ β (风险下限)                          │
│   → 判定分歧不可调和                        │
│   → 自动转入"人工干预"或"外部信息引入"     │
│                                             │
└─────────────────────────────────────────────┘
```

### 任务属性 → 协议选择

| 任务类型 | 推荐协议 | 性能提升 |
|---------|---------|---------|
| 逻辑推理 (编程) | Voting | +13.2% |
| 事实密集 (代码审计) | Consensus | 更优 |

---

## 4. 架构自适应与效能调优

### 功能代码化 (Functional Codification)

当多步协作模式被证明高效且重复出现时:

```
检索 → 审计 → 修复 (高频模式)
         ↓
    自动固化为源代码
         ↓
从"在线推理"转向"代码执行"
         ↓
    如同"肌肉记忆"
```

### 自适应混合协议 (Adaptive Hybrid System)

```python
def route_task(task):
    risk_level = assess_risk(task)

    if risk_level == "low":
        return SingleModelResponse(task)  # 快速响应
    elif risk_level in ["high", "critical"]:
        return FullCouncilDeliberation(task)  # 全理事会审议
```

**高风险任务示例**:

- 代码合并 (git merge)
- 临床诊断
- 金融交易决策

---

## 5. 治理、安全与"人在回路" (HITL)

### 细粒度权限控制 (RBAC)

```yaml
agents:
  web_surfer:
    permissions: [read_web, extract_data]
    restrictions: [no_api_keys, no_env_files]

  coder:
    permissions: [read_code, write_code, run_tests]
    restrictions: [no_delete, no_deploy]

  auditor:
    permissions: [read_only]
    restrictions: [no_write, no_execute]
```

### 关键决策网关

```python
DANGEROUS_OPERATIONS = ["git push", "rm -rf", "DROP TABLE", "deploy"]

def execute(operation):
    if operation in DANGEROUS_OPERATIONS:
        approval = ApprovalRequest(
            operation=operation,
            context=get_current_context(),
            requester="Orchestrator"
        )
        await_human_signature(approval)  # 等待人类"董事长"签字

    return perform(operation)
```

---

## 类比理解

> 编排与决策层就像是一支**顶级医疗专家组的手术室主任**：
>
> 1. 手中握着**病历账本 (Task Ledger)** 实时记录手术进展
> 2. 利用**手术策略标准 (Wald 算法)** 判断何时可以缝合伤口
> 3. 对于常规缝针动作，调用**标准化手术程序 (Functional Codification)**
> 4. 遇到疑难杂症时，通过**圆桌辩论 (Multi-Agent Debate)** 集合各科专家智慧
> 5. 最终签字前，把定案呈报给**您这位董事长 (人类用户)** 过目盖章
