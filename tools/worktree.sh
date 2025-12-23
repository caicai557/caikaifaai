#!/usr/bin/env bash
# Git Worktrees 管理脚本
# 支持多个 Claude Code 会话并行工作在不同的 worktree 中

set -e

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKTREE_BASE="${PROJECT_ROOT}/../worktrees"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 帮助信息
usage() {
    cat << EOF
Git Worktrees 管理工具 - 支持多会话并行开发

用法: 
    $0 create <branch-name> [base-branch]   创建新的 worktree
    $0 list                                  列出所有 worktrees
    $0 remove <branch-name>                  删除 worktree
    $0 clean                                 清理所有 worktrees
    $0 status                                显示所有 worktrees 状态

示例:
    # 创建功能分支的 worktree
    $0 create feature-login main
    
    # 创建 bugfix 的 worktree
    $0 create bugfix-auth-error
    
    # 列出所有 worktrees
    $0 list
    
    # 清理已合并的 worktrees
    $0 clean

EOF
    exit 1
}

# 日志函数
info() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

# 创建 worktree
create_worktree() {
    local branch_name="$1"
    local base_branch="${2:-main}"
    
    if [[ -z "$branch_name" ]]; then
        error "分支名称不能为空"
    fi
    
    # 创建 worktrees 基础目录
    mkdir -p "$WORKTREE_BASE"
    
    local worktree_path="$WORKTREE_BASE/$branch_name"
    
    if [[ -d "$worktree_path" ]]; then
        error "Worktree 已存在: $worktree_path"
    fi
    
    info "创建 worktree: $branch_name (基于 $base_branch)"
    
    cd "$PROJECT_ROOT"
    
    # 检查分支是否存在
    if git rev-parse --verify "$branch_name" >/dev/null 2>&1; then
        # 分支已存在，直接检出
        git worktree add "$worktree_path" "$branch_name"
    else
        # 创建新分支
        git worktree add -b "$branch_name" "$worktree_path" "$base_branch"
    fi
    
    info "Worktree 已创建: $worktree_path"
    info "进入 worktree: cd $worktree_path"
    
    # 复制配置文件
    if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
        cp "$PROJECT_ROOT/.env.example" "$worktree_path/.env"
        info "已复制 .env.example -> .env"
    fi
    
    # 创建软链接到共享的 node_modules（可选）
    if [[ -d "$PROJECT_ROOT/node_modules" ]]; then
        warn "建议在 worktree 中独立安装依赖以避免冲突"
        echo "   运行: cd $worktree_path && pnpm install"
    fi
    
    echo ""
    echo "🚀 下一步:"
    echo "   1. cd $worktree_path"
    echo "   2. pnpm install  # 安装依赖"
    echo "   3. 在新的 Claude Code 窗口中打开此目录"
    echo "   4. 开始并行开发!"
}

# 列出所有 worktrees
list_worktrees() {
    info "当前所有 worktrees:"
    echo ""
    git worktree list
}

# 显示状态
show_status() {
    info "Worktrees 状态:"
    echo ""
    
    git worktree list --porcelain | while IFS= read -r line; do
        if [[ "$line" =~ ^worktree ]]; then
            path="${line#worktree }"
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo "📁 路径: $path"
        elif [[ "$line" =~ ^branch ]]; then
            branch="${line#branch refs/heads/}"
            echo "🌿 分支: $branch"
        fi
    done
    
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 删除 worktree
remove_worktree() {
    local branch_name="$1"
    
    if [[ -z "$branch_name" ]]; then
        error "分支名称不能为空"
    fi
    
    local worktree_path="$WORKTREE_BASE/$branch_name"
    
    if [[ ! -d "$worktree_path" ]]; then
        error "Worktree 不存在: $worktree_path"
    fi
    
    warn "即将删除 worktree: $worktree_path"
    read -p "确认删除? (y/N) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_ROOT"
        git worktree remove "$worktree_path" --force
        info "Worktree 已删除: $branch_name"
        
        read -p "是否删除远程分支? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git branch -D "$branch_name" 2>/dev/null || true
            git push origin --delete "$branch_name" 2>/dev/null || true
            info "分支已删除: $branch_name"
        fi
    else
        info "取消删除"
    fi
}

# 清理所有 worktrees
clean_worktrees() {
    warn "即将清理所有 worktrees（保留 main/master）"
    read -p "确认? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "取消清理"
        return
    fi
    
    cd "$PROJECT_ROOT"
    
    # 获取所有 worktree 路径（排除主仓库）
    git worktree list --porcelain | grep "^worktree" | cut -d' ' -f2 | while read -r path; do
        # 跳过主仓库
        if [[ "$path" == "$PROJECT_ROOT" ]]; then
            continue
        fi
        
        # 获取分支名
        branch=$(git -C "$path" branch --show-current 2>/dev/null || echo "")
        
        if [[ -n "$branch" ]] && [[ "$branch" != "main" ]] && [[ "$branch" != "master" ]]; then
            info "删除 worktree: $path ($branch)"
            git worktree remove "$path" --force
        fi
    done
    
    info "清理完成"
}

# 主逻辑
case "${1:-}" in
    create)
        create_worktree "$2" "$3"
        ;;
    list)
        list_worktrees
        ;;
    status)
        show_status
        ;;
    remove)
        remove_worktree "$2"
        ;;
    clean)
        clean_worktrees
        ;;
    *)
        usage
        ;;
esac
