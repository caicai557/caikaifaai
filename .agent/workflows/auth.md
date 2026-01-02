---
description: 多模型认证配置 - 账号登录和API密钥
---

# /auth 认证配置

## 🔐 认证方式 (2025 最佳实践)

### 方式1: 账号登录 (推荐用于本地开发)

```bash
# 安装 Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# 账号登录 (会打开浏览器)
gcloud auth application-default login

# 设置项目
gcloud config set project YOUR_PROJECT_ID
```

✅ 登录后无需 API Key，自动使用 ADC (Application Default Credentials)

### 方式2: 服务账号 (推荐用于生产环境)

```bash
# 设置环境变量
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 方式3: API 密钥

```bash
# Gemini API Key
export GEMINI_API_KEY="your-key"
# 或
export GOOGLE_API_KEY="your-key"

# Anthropic
export ANTHROPIC_API_KEY="your-key"

# OpenAI
export OPENAI_API_KEY="your-key"
```

## 🔧 模型配置

| 模型 | 标识符 | 用途 |
|------|--------|------|
| Gemini 2.0 Flash | `vertex_ai/gemini-2.0-flash` | 快速执行 |
| Gemini 2.0 Pro | `vertex_ai/gemini-2.0-pro` | 长上下文 (200万) |
| Claude Sonnet 4 | `claude-sonnet-4-20250514` | 精准编码 |
| GPT-4o | `gpt-4o` | 通用 |

## ✅ 验证登录状态

```bash
# 检查当前认证
gcloud auth list

# 测试 Vertex AI 访问
gcloud ai models list --region=us-central1
```
