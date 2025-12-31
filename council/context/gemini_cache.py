"""
Gemini Cache Manager - Gemini API 服务端缓存

2025 最佳实践: 使用 Gemini Context Caching 节省 ~90% Token

使用场景:
- 长文档 Q&A
- 固定系统提示
- 代码库审计

注意:
- 缓存最少 32K Token
- TTL 最短 1 小时，最长 7 天
- 缓存内容使用折扣价格 (~10% 原价)
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import os


@dataclass
class CacheEntry:
    """缓存条目"""

    name: str
    content_hash: str
    token_count: int
    created_at: datetime
    expires_at: datetime
    model: str = "gemini-2.5-pro"


class GeminiCacheManager:
    """
    Gemini API 服务端缓存管理器

    节省策略:
    - 系统提示: 缓存 1 小时
    - 文档内容: 缓存 24 小时
    - 代码库: 缓存 7 天

    Usage:
        cache_mgr = GeminiCacheManager()
        cache_name = cache_mgr.create("system_prompt", system_prompt_text)
        response = cache_mgr.generate_with_cache(cache_name, user_query)
    """

    # 最小缓存大小 (Token)
    MIN_CACHE_TOKENS = 32768  # 32K

    # ... (previous code)

    def __init__(
        self,
        api_key: Optional[str] = None,
        registry_path: str = "~/.council/gemini_cache_registry.json",
    ):
        """
        初始化缓存管理器
        """
        self._api_key = api_key
        self._registry_path = os.path.expanduser(registry_path)
        self._local_cache: Dict[str, CacheEntry] = {}
        self._client = None

        self._load_registry()

    def _load_registry(self):
        """从磁盘加载缓存注册表"""
        try:
            if os.path.exists(self._registry_path):
                import json

                with open(self._registry_path, "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self._local_cache[k] = CacheEntry(
                            name=v["name"],
                            content_hash=v["content_hash"],
                            token_count=v["token_count"],
                            created_at=datetime.fromisoformat(v["created_at"]),
                            expires_at=datetime.fromisoformat(v["expires_at"]),
                            model=v.get("model", "gemini-2.5-pro"),
                        )
        except Exception as e:
            print(f"⚠️ 加载缓存注册表失败: {e}")

    def _save_registry(self):
        """保存缓存注册表到磁盘"""
        try:
            os.makedirs(os.path.dirname(self._registry_path), exist_ok=True)
            import json

            data = {
                k: {
                    "name": v.name,
                    "content_hash": v.content_hash,
                    "token_count": v.token_count,
                    "created_at": v.created_at.isoformat(),
                    "expires_at": v.expires_at.isoformat(),
                    "model": v.model,
                }
                for k, v in self._local_cache.items()
            }
            with open(self._registry_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ 保存缓存注册表失败: {e}")


    def _clean_expired(self):
        """清理过期缓存"""
        now = datetime.now()
        expired = [k for k, v in self._local_cache.items() if v.expires_at <= now]
        for k in expired:
            del self._local_cache[k]
        if expired:
            self._save_registry()

    # ... (rest of methods)

    def _get_client(self):
        """获取 Gemini 客户端 (延迟初始化)"""
        if self._client is None:
            try:
                import google.generativeai as genai

                if self._api_key:
                    genai.configure(api_key=self._api_key)
                self._client = genai
            except ImportError:
                raise ImportError(
                    "google-generativeai 未安装。"
                    "请运行: pip install google-generativeai"
                )
        return self._client

    def _estimate_tokens(self, content: str) -> int:
        """估算 Token 数量 (简单估算)"""
        # 中文约 1.5 字符/token，英文约 4 字符/token
        # 取保守估算
        return max(len(content) // 3, 100)

    def _content_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def can_cache(self, content: str) -> tuple[bool, str]:
        """
        检查内容是否可以缓存

        Returns:
            (可否缓存, 原因)
        """
        tokens = self._estimate_tokens(content)
        if tokens < self.MIN_CACHE_TOKENS:
            return (
                False,
                f"内容太短 ({tokens} tokens < {self.MIN_CACHE_TOKENS} 最小要求)",
            )
        return True, f"可以缓存 (~{tokens} tokens)"

    def create(
        self, name: str, content: str, ttl_hours: int = 1, model: str = "gemini-2.5-pro"
    ) -> Optional[str]:
        """
        创建缓存

        Args:
            name: 缓存名称 (用于标识)
            content: 要缓存的内容
            ttl_hours: 缓存有效期 (小时)
            model: 使用的模型

        Returns:
            缓存 ID，如果创建失败返回 None
        """
        can_cache, reason = self.can_cache(content)
        if not can_cache:
            print(f"⚠️ 无法缓存 '{name}': {reason}")
            return None

        content_hash = self._content_hash(content)

        # 检查是否已有相同内容的缓存
        for cached_name, entry in self._local_cache.items():
            if entry.content_hash == content_hash:
                if entry.expires_at > datetime.now():
                    print(f"✅ 复用已有缓存: {cached_name}")
                    return cached_name

        try:
            genai = self._get_client()

            # 创建服务端缓存
            cache = genai.caching.CachedContent.create(
                model=model,
                display_name=name,
                contents=[{"parts": [{"text": content}]}],
                ttl=timedelta(hours=ttl_hours),
            )

            # 记录本地缓存信息
            self._local_cache[cache.name] = CacheEntry(
                name=cache.name,
                content_hash=content_hash,
                token_count=self._estimate_tokens(content),
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=ttl_hours),
                model=model,
            )

            print(f"✅ 缓存已创建: {cache.name} (TTL: {ttl_hours}h)")
            return cache.name

        except Exception as e:
            print(f"❌ 创建缓存失败: {e}")
            return None

    def generate_with_cache(
        self,
        cache_name: str,
        query: str,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        使用缓存进行推理

        Args:
            cache_name: 缓存 ID
            query: 用户查询
            generation_config: 生成配置

        Returns:
            生成的响应文本
        """
        try:
            genai = self._get_client()

            # 获取缓存
            cache = genai.caching.CachedContent.get(cache_name)

            # 使用缓存的模型生成
            model = genai.GenerativeModel.from_cached_content(cache)
            response = model.generate_content(
                query, generation_config=generation_config
            )

            return response.text

        except Exception as e:
            print(f"❌ 使用缓存生成失败: {e}")
            return None

    def delete(self, cache_name: str) -> bool:
        """删除缓存"""
        try:
            genai = self._get_client()
            genai.caching.CachedContent.get(cache_name).delete()
            self._local_cache.pop(cache_name, None)
            print(f"✅ 缓存已删除: {cache_name}")
            return True
        except Exception as e:
            print(f"❌ 删除缓存失败: {e}")
            return False

    def list_caches(self) -> List[CacheEntry]:
        """列出所有缓存"""
        # 清理过期缓存
        now = datetime.now()
        self._local_cache = {
            k: v for k, v in self._local_cache.items() if v.expires_at > now
        }
        return list(self._local_cache.values())

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        caches = self.list_caches()
        total_tokens = sum(c.token_count for c in caches)
        return {
            "cache_count": len(caches),
            "total_tokens_cached": total_tokens,
            "estimated_savings_percent": 90 if caches else 0,
        }


# 导出
__all__ = [
    "GeminiCacheManager",
    "CacheEntry",
]
