"""
Hub Module - 枢纽-辐辏模型核心
实现中央共享上下文存储器和发布/订阅机制。
"""

import logging
from typing import Callable, Dict, List, Optional
from collections import defaultdict

from council.orchestration.events import Event, EventType
from council.orchestration.ledger import DualLedger

# 类型定义: 订阅回调函数
# Callback(event: Event) -> None
SubscriptionCallback = Callable[[Event], None]

# 常量
MAX_HISTORY = 1000
MAX_PUBLISH_DEPTH = 10


class Hub:
    """
    MCP 枢纽 (The Hub)

    功能:
    1. 中央消息总线 (Pub/Sub)
    2. 共享上下文持有者 (Holds DualLedger)
    3. 自动化的"接力"逻辑 (Auto-dispatch)
    """

    def __init__(self, ledger: Optional[DualLedger] = None):
        self._subscribers: Dict[EventType, List[SubscriptionCallback]] = defaultdict(
            list
        )
        self._ledger = ledger
        self._history: List[Event] = []
        self._publish_depth = 0  # 递归深度保护
        self.logger = logging.getLogger("Hub")

    @property
    def ledger(self) -> Optional[DualLedger]:
        """获取关联的账本"""
        return self._ledger

    @ledger.setter
    def ledger(self, ledger: DualLedger):
        self._ledger = ledger

    def subscribe(self, event_type: EventType, callback: SubscriptionCallback) -> None:
        """
        订阅特定类型的事件

        Args:
            event_type: 感兴趣的事件类型
            callback: 回调函数
        """
        self._subscribers[event_type].append(callback)
        self.logger.debug(f"Subscribed to {event_type.value}: {callback.__name__}")

    def unsubscribe(
        self, event_type: EventType, callback: SubscriptionCallback
    ) -> None:
        """
        取消订阅

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    def publish(self, event: Event) -> None:
        """
        发布事件

        Args:
            event: 事件对象
        """
        # 递归深度保护
        if self._publish_depth >= MAX_PUBLISH_DEPTH:
            self.logger.error(
                f"Publish depth exceeded ({MAX_PUBLISH_DEPTH}), dropping event"
            )
            return

        self._publish_depth += 1
        try:
            self.logger.info(
                f"Event Published: [{event.type.value}] from {event.source}"
            )

            # 1. 记录历史 (带容量限制)
            self._history.append(event)
            if len(self._history) > MAX_HISTORY:
                self._history = self._history[-MAX_HISTORY:]

            # 2. 更新内部状态 (Ledger Integration)
            self._update_ledger(event)

            # 3. 分发给订阅者 (Automated Relay)
            if event.type in self._subscribers:
                subscribers = self._subscribers[event.type]
                self.logger.info(
                    f"Relaying event [{event.type.value}] to {len(subscribers)} subscribers"
                )

                for callback in subscribers:
                    try:
                        callback(event)
                    except Exception as e:
                        self.logger.error(
                            f"Error in subscriber {callback.__name__}: {e}"
                        )
            else:
                self.logger.debug(f"No subscribers for event [{event.type.value}]")
        finally:
            self._publish_depth -= 1

    def _update_ledger(self, event: Event) -> None:
        """
        根据事件自动更新账本 (Internal Logic)
        """
        if not self._ledger:
            return

        payload = event.payload

        # 自动处理信息流事件
        if event.type == EventType.FACT_DISCOVERED:
            key = payload.get("key")
            value = payload.get("value")
            if key and value:
                self._ledger.task.add_fact(key, value)

        elif event.type == EventType.QUERY_RAISED:
            query = payload.get("query")
            if query:
                self._ledger.task.add_query(query)

        elif event.type == EventType.QUERY_RESOLVED:
            query = payload.get("query")
            result = payload.get("result")
            if query and result:
                self._ledger.task.resolve_query(query, result)

        # 自动处理进度记录
        elif event.type in [
            EventType.CODE_WRITTEN,
            EventType.TEST_PASSED,
            EventType.TEST_FAILED,
        ]:
            action = f"Event: {event.type.value}"
            result = str(payload)
            is_progress = event.type in [EventType.CODE_WRITTEN, EventType.TEST_PASSED]
            self._ledger.progress.record_iteration(
                progress=is_progress, action=action, result=result
            )

    def get_recent_events(self, limit: int = 10) -> List[Event]:
        """获取最近的事件"""
        return self._history[-limit:]

    def get_context(self) -> str:
        """
        获取当前共享上下文 (Single Source of Truth)

        Returns:
            Formatted string of the Ledger state
        """
        if self._ledger:
            return self._ledger.get_full_context()
        return "No Ledger attached to Hub."
