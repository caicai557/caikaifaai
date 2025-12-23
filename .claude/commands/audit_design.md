---
description: "架构审计: 全库扫描,发现潜在冲突,输出技术设计文档"
---

# 架构审计命令

## 用途
利用超长上下文窗口扫描整个代码库，发现新方案与旧逻辑的潜在冲突，输出详细的技术设计文档。

## 主控者
**Gemini 1.5 Pro (200万 tokens 上下文)** - 架构师角色

## 执行方式
```bash
# 通过 MCP 调用 gemini 工具
gpp "Audit design for: $ARGUMENTS. Review entire codebase for conflicts."
```

## 输入
- PRD 文档 (prd_output.yaml)
- 任务树 (task_tree.yaml)
- 整个代码库上下文

## 输出格式 (YAML)

```yaml
audit_report:
  timestamp: "2025-12-22T12:00:00Z"
  prd_reference: "prd_output.yaml"
  
  codebase_scan:
    total_files_scanned: 150
    total_lines: 45000
    key_dependencies:
      - name: "react"
        version: "18.2.0"
      - name: "typescript"
        version: "5.0.0"
  
  conflicts:
    - severity: "blocker | major | minor"
      title: "冲突标题"
      description: |
        新方案与旧逻辑的具体冲突描述
      affected_components:
        - path: "src/auth/legacy-auth.ts"
          lines: "45-67"
      impact: "影响范围和后果"
      recommendation: "建议的解决方案"
  
  design_decisions:
    - decision: "使用 JWT 而不是 Session"
      rationale: |
        - 无状态,易于横向扩展
        - 减少服务器内存压力
      tradeoffs:
        pros:
          - 扩展性好
        cons:
          - 无法即时撤销 token
      alternatives_considered:
        - "Session + Redis"
        - "OAuth2"
  
  architecture_patterns:
    - pattern: "Repository Pattern"
      location: "src/repositories/"
      justification: "数据访问层抽象,便于测试和切换数据源"
  
  data_flow:
    - component: "UserLoginFlow"
      diagram: |
        Client -> API Gateway -> Auth Service -> User DB
                                              -> JWT Generator
                             <- JWT Token <-
      critical_paths:
        - "密码验证失败时的错误处理"
        - "JWT 刷新机制"
  
  technical_design:
    file_structure:
      new_files:
        - path: "src/auth/jwt-service.ts"
          exports:
            - "generateToken()"
            - "verifyToken()"
        - path: "src/auth/password-hasher.ts"
          exports:
            - "hashPassword()"
            - "comparePassword()"
      modified_files:
        - path: "src/api/routes.ts"
          changes: "添加 /login, /logout 路由"
    
    interfaces:
      - name: "IAuthService"
        methods:
          - "login(email: string, password: string): Promise<AuthToken>"
          - "logout(token: string): Promise<void>"
    
    database_changes:
      - table: "users"
        new_columns:
          - name: "last_login_at"
            type: "TIMESTAMP"
        indexes:
          - columns: ["email"]
            unique: true
  
  security_considerations:
    - concern: "密码存储"
      solution: "使用 bcrypt,成本因子 12"
    - concern: "JWT 密钥管理"
      solution: "从环境变量读取,定期轮换"
  
  performance_impact:
    - area: "密码哈希"
      estimated_latency: "~200ms per login"
      mitigation: "异步处理,客户端显示加载状态"
  
  testing_strategy:
    unit_tests:
      - "JWT 生成和验证"
      - "密码哈希和比较"
    integration_tests:
      - "完整登录流程"
      - "错误凭证处理"
    e2e_tests:
      - "用户从注册到登录全流程"

verification:
  - cmd: "yq '.audit_report.conflicts | length' audit_output.yaml"
    expected: "显示冲突数量"
  - cmd: "yq '.audit_report.technical_design.file_structure.new_files' audit_output.yaml"
    expected: "显示新文件列表"

next_steps:
  - "审查 conflicts,优先解决 blocker 级别"
  - "确认 design_decisions,与团队讨论"
  - "将 technical_design 转换为实施任务"
  - "调用 /tdd_tests 生成测试用例"
```

## 使用示例

```bash
# 在 Claude Code 中调用
/audit_design "用户登录功能的架构审计"
```

## 验证步骤
1. 检查是否扫描了所有相关文件
2. 验证冲突列表的完整性
3. 确认设计决策有明确的 rationale
4. 检查是否包含数据流图
5. 验证安全考虑是否覆盖 OWASP Top 10

## 质量标准
- **完整性**: 覆盖所有受影响的组件
- **准确性**: 冲突描述精确到文件和行号
- **可操作性**: 每个冲突都有明确的 recommendation
- **前瞻性**: 考虑了扩展性和维护性

## 下游命令
- 设计批准后 → `/tdd_tests` (生成测试)
- 发现冲突时 → `/codex_patch_plan` (修复冲突)
