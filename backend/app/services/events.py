"""Domain event publishing stub.

A real event store/outbox will replace this later; consumers are wired now
so that presence.started.v1 and presence.ended.v1 are emitted from the use
cases themselves.
"""

from __future__ import annotations


class EventPublisher:
    async def publish(
        self, event_type: str, entity_id: str, actor_user_id: str | None = None
    ) -> None:
        pass


event_publisher = EventPublisher()