# 🚀 快速开始 (Quick Start)

**5 分钟完成项目设置**

---

## 📋 前提条件

- Python 3.12+
- Git
- Claude Pro/Max 或 Gemini API 账号

---

## Step 1: 安装

```bash
# 克隆项目
git clone <repo-url>
cd cesi-council

# 推荐: 使用 uv (10x 快于 pip)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -e ".[dev]"

# 备选: 传统 pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Step 2: 登录 (账号认证 - 非 API Key)

### Claude Code

```bash
claude login
# 浏览器会自动打开，完成 OAuth 登录
```

### Gemini CLI

```bash
gemini
# 选择 "Login with Google"
# 浏览器完成认证
```

> ⚠️ **重要**: 本地开发使用账号登录，不需要 API Key！
> API Key 仅用于 CI/CD 自动化。

---

## Step 3: 验证

```bash
just check
```

输出应该显示:

```
=== Council Setup Check ===
✅ Python 3.12+
✅ Required packages installed
✅ Claude authenticated
✅ Gemini authenticated
🎉 All checks passed!
```

---

## Step 4: 开始开发

```bash
# 运行测试
just test

# 启动开发工作流
just dev "你的任务描述"
```

---

## 🆘 常见问题

### Q: `just` 命令找不到？

```bash
# 安装 just
cargo install just
# 或
brew install just
```

### Q: 登录失败？

```bash
# 重新登录
claude logout && claude login
```

### Q: 依赖安装失败？

```bash
# 使用 uv 重试
uv pip install -e ".[dev]" --reinstall
```

---

## 📚 下一步

- 阅读 [CLAUDE.md](./CLAUDE.md) 了解项目架构
- 阅读 [CODEMAP.md](./CODEMAP.md) 查看代码地图
- 运行 `just dev "任务"` 开始开发
