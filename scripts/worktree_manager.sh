#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-}"
BRANCH="${2:-}"

if [[ -z "${ACTION}" || -z "${BRANCH}" ]]; then
  echo "Usage: scripts/worktree_manager.sh <create|remove|list> <branch>" >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
WORKTREE_ROOT="${WORKTREE_ROOT:-${ROOT}/../cesi.worktrees}"
mkdir -p "${WORKTREE_ROOT}"
WORKTREE_ROOT="$(cd "${WORKTREE_ROOT}" && pwd)"
WORKTREE_PATH="${WORKTREE_ROOT}/${BRANCH}"

case "${ACTION}" in
  create)
    if [[ -e "${WORKTREE_PATH}" ]]; then
      if git worktree list --porcelain | grep -Fq "worktree ${WORKTREE_PATH}"; then
        echo "Worktree already exists: ${WORKTREE_PATH}"
        exit 0
      fi
      echo "Path exists but is not a worktree: ${WORKTREE_PATH}" >&2
      exit 1
    fi
    if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
      git worktree add -B "${BRANCH}" "${WORKTREE_PATH}"
    else
      git worktree add -b "${BRANCH}" "${WORKTREE_PATH}"
    fi
    ;;
  remove)
    if git worktree list --porcelain | grep -Fq "worktree ${WORKTREE_PATH}"; then
      git worktree remove --force "${WORKTREE_PATH}"
      git worktree prune
    else
      echo "Worktree not registered: ${WORKTREE_PATH}" >&2
      exit 1
    fi
    ;;
  list)
    git worktree list
    ;;
  *)
    echo "Unknown action: ${ACTION}" >&2
    exit 1
    ;;
esac
