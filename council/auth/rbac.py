"""
RBAC (Role-Based Access Control) 权限系统
实现最小权限原则，为每个智能体分配细粒度权限
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Set, Optional
import fnmatch


class Permission(Enum):
    """权限级别枚举"""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"


class Role(Enum):
    """角色定义"""

    AUDITOR = "auditor"  # 只读权限，审计员
    ENGINEER = "engineer"  # 读写权限，工程师
    ARCHITECT = "architect"  # 读写+设计权限
    ADMIN = "admin"  # 全部权限
    CODER = "coder"  # 代码读写权限


@dataclass
class RolePermissions:
    """角色权限配置"""

    role: Role
    permissions: Set[Permission]
    allowed_paths: Set[str] = field(default_factory=set)
    denied_paths: Set[str] = field(default_factory=set)


# 敏感路径黑名单 - 所有角色禁止访问
SENSITIVE_PATHS = {
    ".ssh/",
    ".ssh/*",
    "**/.ssh/**",
    ".env",
    "*.env",
    ".env.*",
    "**/.env",
    "secrets/",
    "secrets/**",
    "**/secrets/**",
    "*.key",
    "*.pem",
    "*.p12",
    "**/credentials/**",
    ".aws/",
    ".gcp/",
}


# 默认角色权限矩阵
DEFAULT_ROLE_PERMISSIONS = {
    Role.AUDITOR: RolePermissions(
        role=Role.AUDITOR,
        permissions={Permission.READ},
        allowed_paths={"**/*"},
        denied_paths=SENSITIVE_PATHS,
    ),
    Role.CODER: RolePermissions(
        role=Role.CODER,
        permissions={Permission.READ, Permission.WRITE},
        allowed_paths={"src/**", "tests/**", "*.py", "*.ts", "*.js"},
        denied_paths=SENSITIVE_PATHS | {"config/**", "deploy/**"},
    ),
    Role.ENGINEER: RolePermissions(
        role=Role.ENGINEER,
        permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE},
        allowed_paths={"**/*"},
        denied_paths=SENSITIVE_PATHS | {"deploy/**"},
    ),
    Role.ARCHITECT: RolePermissions(
        role=Role.ARCHITECT,
        permissions={Permission.READ, Permission.WRITE},
        allowed_paths={"**/*"},
        denied_paths=SENSITIVE_PATHS,
    ),
    Role.ADMIN: RolePermissions(
        role=Role.ADMIN,
        permissions={
            Permission.READ,
            Permission.WRITE,
            Permission.EXECUTE,
            Permission.DELETE,
            Permission.ADMIN,
        },
        allowed_paths={"**/*"},
        denied_paths=set(),  # Admin 可以访问所有路径
    ),
}


class RBAC:
    """
    基于角色的访问控制系统

    使用示例:
        rbac = RBAC()

        # 检查权限
        if rbac.check_permission(Role.CODER, Permission.WRITE, "src/main.py"):
            # 允许操作
            pass
    """

    def __init__(self, custom_permissions: Optional[dict] = None):
        """
        初始化 RBAC 系统

        Args:
            custom_permissions: 自定义角色权限配置，覆盖默认配置
        """
        self.permissions = DEFAULT_ROLE_PERMISSIONS.copy()
        if custom_permissions:
            self.permissions.update(custom_permissions)

    def _match_path(self, path: str, patterns: Set[str]) -> bool:
        """
        检查路径是否匹配任一 glob 模式

        Args:
            path: 要检查的路径
            patterns: glob 模式集合

        Returns:
            是否匹配
        """
        path = str(Path(path))
        for pattern in patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
            # 检查路径中的任意部分
            if "**" in pattern:
                # 简化的 ** 匹配
                simple_pattern = pattern.replace("**", "*")
                if fnmatch.fnmatch(path, simple_pattern):
                    return True
        return False

    def check_permission(
<<<<<<< HEAD
        self,
        role: Role,
        permission: Permission,
        path: Optional[str] = None
=======
        self, role: Role, permission: Permission, path: Optional[str] = None
>>>>>>> e2df45bcf4fae044c2ec81c7ea50a183bdc8bd86
    ) -> bool:
        """
        检查角色是否有指定权限

        Args:
            role: 角色
            permission: 请求的权限
            path: 可选的路径，用于路径级别权限检查

        Returns:
            是否有权限
        """
        if role not in self.permissions:
            return False

        role_perms = self.permissions[role]

        # 检查基本权限
        if permission not in role_perms.permissions:
            return False

        # 如果没有指定路径，只检查基本权限
        if path is None:
            return True

        # 检查路径权限
        # 首先检查是否在黑名单中
        if self._match_path(path, role_perms.denied_paths):
            return False

        # 然后检查是否在白名单中
        if role_perms.allowed_paths and not self._match_path(
            path, role_perms.allowed_paths
        ):
            return False

        return True

    def get_role_summary(self, role: Role) -> dict:
        """
        获取角色权限摘要

        Args:
            role: 角色

        Returns:
            权限摘要字典
        """
        if role not in self.permissions:
            return {"error": f"Unknown role: {role}"}

        perms = self.permissions[role]
        return {
            "role": role.value,
            "permissions": [p.value for p in perms.permissions],
            "allowed_paths": list(perms.allowed_paths),
            "denied_paths": list(perms.denied_paths),
        }

    def is_sensitive_path(self, path: str) -> bool:
        """
        检查路径是否为敏感路径

        Args:
            path: 路径

        Returns:
            是否为敏感路径
        """
        return self._match_path(path, SENSITIVE_PATHS)


# 导出
__all__ = ["Permission", "Role", "RolePermissions", "RBAC", "SENSITIVE_PATHS"]
