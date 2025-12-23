---
description: "TDD 测试生成: 在编写代码前强制生成测试,覆盖率 ≥90%"
---

# TDD 测试生成命令

## 用途
在编写逻辑前，根据设计文档生成完整的测试用例。强制执行 TDD 原则：测试覆盖率未达 90% 严禁进入执行阶段。

## 主控者
**Claude Code** - QA 角色

## 前置条件
- 已完成 `/prd_generate` 
- 已完成 `/audit_design`
- 已有技术设计文档 (audit_output.yaml)

## 执行方式
```bash
# 在 Claude Code 中调用
/tdd_tests "为 <功能名称> 生成测试用例"
```

## 输出格式 (JSON)

```json
{
  "test_suite": {
    "name": "UserAuthenticationTests",
    "framework": "Jest | Vitest | Pytest | Go Test",
    "coverage_target": 90,
    
    "unit_tests": [
      {
        "file": "src/auth/jwt-service.test.ts",
        "description": "JWT 服务单元测试",
        "test_cases": [
          {
            "name": "should generate valid JWT token",
            "setup": "const userId = 'user-123'",
            "action": "const token = generateToken(userId)",
            "assertion": "expect(verifyToken(token).userId).toBe('user-123')",
            "edge_cases": [
              "空 userId",
              "超长 userId (>1000 chars)",
              "特殊字符 userId"
            ]
          },
          {
            "name": "should reject expired token",
            "setup": "const token = generateToken('user-123', { expiresIn: '1ms' })",
            "action": "await sleep(10); verifyToken(token)",
            "assertion": "expect(() => verifyToken(token)).toThrow('Token expired')"
          }
        ],
        "dependencies": [
          "jsonwebtoken"
        ],
        "mocks": []
      }
    ],
    
    "integration_tests": [
      {
        "file": "src/auth/auth-flow.test.ts",
        "description": "登录流程集成测试",
        "test_cases": [
          {
            "name": "should login with valid credentials",
            "setup": "await createTestUser('test@example.com', 'Password123!')",
            "action": "const result = await authService.login('test@example.com', 'Password123!')",
            "assertion": "expect(result.token).toBeDefined()",
            "cleanup": "await deleteTestUser('test@example.com')"
          },
          {
            "name": "should reject invalid password",
            "setup": "await createTestUser('test@example.com', 'Password123!')",
            "action": "authService.login('test@example.com', 'WrongPassword')",
            "assertion": "expect(error.code).toBe('INVALID_CREDENTIALS')"
          }
        ],
        "dependencies": [
          "database test instance",
          "auth service"
        ],
        "mocks": []
      }
    ],
    
    "e2e_tests": [
      {
        "file": "tests/e2e/login.spec.ts",
        "description": "端到端登录测试",
        "framework": "Playwright | Cypress",
        "test_cases": [
          {
            "name": "User can login via UI",
            "steps": [
              "访问 /login 页面",
              "输入邮箱 test@example.com",
              "输入密码 Password123!",
              "点击登录按钮",
              "等待跳转到 /dashboard"
            ],
            "assertion": "页面 URL 应为 /dashboard",
            "screenshot": true
          },
          {
            "name": "Error message shown for wrong password",
            "steps": [
              "访问 /login 页面",
              "输入邮箱 test@example.com",
              "输入错误密码 WrongPass",
              "点击登录按钮"
            ],
            "assertion": "显示错误消息 'Invalid credentials'"
          }
        ]
      }
    ],
    
    "security_tests": [
      {
        "file": "src/auth/security.test.ts",
        "description": "安全测试",
        "test_cases": [
          {
            "name": "Password should be hashed before storage",
            "action": "const user = await createUser('test@example.com', 'plaintext')",
            "assertion": "expect(user.password).not.toBe('plaintext')"
          },
          {
            "name": "Should prevent SQL injection in login",
            "action": "authService.login(\"' OR '1'='1\", 'anything')",
            "assertion": "expect(error.code).toBe('INVALID_CREDENTIALS')"
          },
          {
            "name": "Should rate limit login attempts",
            "action": "for(let i=0; i<10; i++) { await authService.login('test@example.com', 'wrong') }",
            "assertion": "expect(error.code).toBe('RATE_LIMIT_EXCEEDED')"
          }
        ]
      }
    ],
    
    "performance_tests": [
      {
        "file": "src/auth/perf.test.ts",
        "description": "性能测试",
        "test_cases": [
          {
            "name": "Password hashing should complete within 500ms",
            "action": "const start = Date.now(); await hashPassword('test123'); const duration = Date.now() - start",
            "assertion": "expect(duration).toBeLessThan(500)"
          }
        ]
      }
    ],
    
    "coverage_requirements": {
      "overall": 90,
      "per_file": {
        "src/auth/jwt-service.ts": 95,
        "src/auth/password-hasher.ts": 95,
        "src/auth/auth-service.ts": 90
      },
      "uncovered_acceptable": [
        "Error handling for unreachable external services"
      ]
    }
  },
  
  "test_data": {
    "fixtures": [
      {
        "name": "validUser",
        "data": {
          "email": "test@example.com",
          "password": "Password123!",
          "hashedPassword": "$2b$12$..."
        }
      }
    ],
    "factories": [
      {
        "name": "createTestUser",
        "params": ["email", "password"],
        "returns": "User object with hashed password"
      }
    ]
  },
  
  "ci_integration": {
    "pre_commit_hook": "npm run test:unit",
    "pr_check": "npm run test:all && npm run test:coverage",
    "coverage_threshold": {
      "statements": 90,
      "branches": 85,
      "functions": 90,
      "lines": 90
    }
  },
  
  "verification": [
    {
      "cmd": "npm test -- --coverage",
      "expected": "Coverage ≥ 90%"
    },
    {
      "cmd": "npm test -- --listTests",
      "expected": "显示所有测试文件"
    }
  ]
}
```

## 生成后验证

### 1. 覆盖率检查
```bash
npm run test:coverage
# 或
pytest --cov=src --cov-report=term --cov-fail-under=90
```

**阻断条件**: 如果覆盖率 < 90%，禁止执行 `/codex_patch_plan` 或开始编写代码

### 2. 测试可执行性
```bash
npm test -- --dry-run
```

### 3. 边界条件覆盖
检查是否包含：
- ✅ 空值/null 处理
- ✅ 极端值测试 (最大/最小)
- ✅ 并发/竞态条件
- ✅ 错误路径测试
- ✅ 安全测试 (SQL注入, XSS, CSRF)

## 使用示例

```bash
# 完整流程
/prd_generate "用户登录功能"
/audit_design "登录功能架构审计"
/tdd_tests "为登录功能生成测试"

# 验证测试覆盖率
npm run test:coverage

# 如果覆盖率 < 90%，重新生成或手动补充测试
# 直到达标后才能进入下一步
```

## 测试优先级

1. **P0 - 阻断级**: 
   - 核心功能路径 (happy path)
   - 安全相关 (认证/授权)
   - 数据完整性

2. **P1 - 重要**:
   - 错误处理路径
   - 边界条件
   - 性能关键路径

3. **P2 - 增强**:
   - UI 交互细节
   - 兼容性测试
   - 极端边界情况

## 下游命令
- 测试覆盖率达标 → `/batch_executor` (执行实现)
- 测试覆盖率不达标 → 重新运行 `/tdd_tests` 补充测试
- 发现设计缺陷 → 返回 `/audit_design` 修正设计
