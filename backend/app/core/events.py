"""
DSRA V2 — Event Broker & SSE Publisher
========================================
Manages in-memory message queues for streaming Server-Sent Events (SSE)
to active research clients.
"""

import asyncio
from typing import AsyncGenerator
from uuid import UUID

from app.core.logging import get_logger
from app.schemas.common import SSEEvent, SSEEventType

log = get_logger(__name__)


class EventBroker:
    """
    In-memory pub-sub broker for session-specific events.
    Allows API handlers to subscribe to real-time agent execution events.
    """

    def __init__(self) -> None:
        # Maps session_id (UUID) to a set of active asyncio.Queues
        self._listeners: dict[UUID, set[asyncio.Queue[SSEEvent]]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, session_id: UUID) -> AsyncGenerator[SSEEvent, None]:
        """Subscribe to a session event stream. Yields SSEEvent objects."""
        queue: asyncio.Queue[SSEEvent] = asyncio.Queue()
        async with self._lock:
            if session_id not in self._listeners:
                self._listeners[session_id] = set()
            self._listeners[session_id].add(queue)

        log.debug("sse_client_subscribed", session_id=str(session_id))
        try:
            while True:
                event = await queue.get()
                yield event
                queue.task_done()
        except asyncio.CancelledError:
            log.debug("sse_client_connection_cancelled", session_id=str(session_id))
        finally:
            async with self._lock:
                if session_id in self._listeners:
                    self._listeners[session_id].discard(queue)
                    if not self._listeners[session_id]:
                        del self._listeners[session_id]

    async def publish(self, session_id: UUID, event: SSEEvent) -> None:
        """Publish an event to all active listeners for a session."""
        async with self._lock:
            queues = self._listeners.get(session_id, set()).copy()

        if not queues:
            log.debug("no_active_listeners_for_event", session_id=str(session_id), event=event.event)
            return

        for queue in queues:
            await queue.put(event)
        log.debug("sse_event_published", session_id=str(session_id), event=event.event)


# Global singleton instance
event_broker = EventBroker()
