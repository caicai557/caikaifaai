#!/usr/bin/env bash
# Council 1.0.0 一键启动脚本

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}
   ____                      _ _ 
  / ___|___  _   _ _ __   ___(_) |
 | |   / _ \\| | | | '_ \\ / __| | |
 | |__| (_) | |_| | | | | (__| | |
  \\____\\___/ \\__,_|_| |_|\\___|_|_|
  
  Multi-Agent Council Framework v1.0.0
${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${BLUE}📦 安装依赖...${NC}"
if command -v uv &> /dev/null; then
    echo -e "${GREEN}⚡ 使用 uv${NC}"
    uv sync --all-extras 2>/dev/null || pip install -e ".[all]"
else
    pip install -e ".[all]"
fi

echo -e "\n${BLUE}🔑 检测 API Keys...${NC}"
[ -n "$GEMINI_API_KEY" ] && echo -e "${GREEN}  ✅ GEMINI_API_KEY${NC}" || echo -e "${YELLOW}  ⚠️ GEMINI_API_KEY 未设置${NC}"
[ -n "$OPENAI_API_KEY" ] && echo -e "${GREEN}  ✅ OPENAI_API_KEY${NC}" || echo -e "${YELLOW}  ⚠️ OPENAI_API_KEY 未设置${NC}"
[ -n "$ANTHROPIC_API_KEY" ] && echo -e "${GREEN}  ✅ ANTHROPIC_API_KEY${NC}" || echo -e "${YELLOW}  ⚠️ ANTHROPIC_API_KEY 未设置${NC}"

echo -e "\n${BLUE}🧪 验证安装...${NC}"
python3 -c "from council import ModelRouter, RedisDistributedLock, SSEFormatter, ProgrammaticToolExecutor; print('  ✅ Council 1.0.0 模块加载成功')"

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🚀 Council 1.0.0 准备就绪!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e ""
echo -e "${BLUE}CLI 命令:${NC}"
echo -e "  ${YELLOW}council status${NC}               # 查看系统状态"
echo -e "  ${YELLOW}council dev \"任务描述\"${NC}       # 一键开发"
echo -e "  ${YELLOW}council classify <任务>${NC}      # 分类并推荐模型"
