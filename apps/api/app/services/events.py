from __future__ import annotations

from collections import defaultdict

from fastapi import WebSocket

from app.schemas.models import EventMessage


class EventBroker:
    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, incident_id: str, socket: WebSocket) -> None:
        await socket.accept()
        self.connections[incident_id].add(socket)

    def disconnect(self, incident_id: str, socket: WebSocket) -> None:
        self.connections[incident_id].discard(socket)

    async def publish(self, event_type: str, incident_id: str, data: dict) -> None:
        event = EventMessage(type=event_type, incident_id=incident_id, data=data)
        stale: list[WebSocket] = []
        for socket in self.connections[incident_id]:
            try:
                await socket.send_json(event.model_dump(mode="json"))
            except Exception:
                stale.append(socket)
        for socket in stale:
            self.disconnect(incident_id, socket)
