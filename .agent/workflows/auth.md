---
description: 多模型认证配置 - 账号登录和API密钥
---

# /auth 认证配置

## 🔐 认证状态

| 模型 | CLI | 认证文件 | 状态 |
|------|-----|----------|------|
| **Gemini** | `gemini` | `~/.gemini/oauth_creds.json` | ✅ |
| **Codex** | `codex` | `~/.codex/auth.json` | ✅ |
| **Claude** | `claude` | `~/.claude/auth.json` | 检查 |

## 🔑 账号登录命令

### Gemini (Google)

```bash
# 已通过 gemini CLI 登录
# 凭据: ~/.gemini/oauth_creds.json
```

### Codex (OpenAI)

```bash
# 方式1: ChatGPT 账号登录 (推荐)
codex login

# 方式2: 无头环境
codex login --device-auth
```

### Claude (Anthropic)

```bash
# 方式1: 账号登录
claude login

# 方式2: API Key
export ANTHROPIC_API_KEY="your-key"
```

## 📁 凭据位置

```
~/.gemini/oauth_creds.json     # Gemini OAuth
~/.codex/auth.json             # Codex OAuth  
~/.config/gcloud/application_default_credentials.json  # ADC (共享)
```

## ✅ 验证认证

```bash
# Gemini
gemini --version

# Codex
codex --version

# Claude
claude --version
```

## 🔧 Council 项目配置

Council 自动检测以下凭据 (优先级):

1. `GEMINI_API_KEY` / `GOOGLE_API_KEY`
2. `~/.config/gcloud/application_default_credentials.json`
3. `OPENAI_API_KEY`
4. `ANTHROPIC_API_KEY`
