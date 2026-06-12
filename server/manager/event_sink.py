from typing import Any, Dict, List, Optional, Protocol, Tuple


class EventSink(Protocol):
    async def broadcast(self, room_id: str, message: Dict[str, Any]) -> None:
        ...

    async def send_to_player(self, room_id: str, player_name: str, message: Dict[str, Any]) -> None:
        ...

    async def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        ...


class NullEventSink:
    async def broadcast(self, room_id: str, message: Dict[str, Any]) -> None:
        return None

    async def send_to_player(self, room_id: str, player_name: str, message: Dict[str, Any]) -> None:
        return None

    async def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        return None


class RecordingEventSink:
    def __init__(self) -> None:
        self.broadcasts: List[Tuple[str, Dict[str, Any]]] = []
        self.player_messages: List[Tuple[str, str, Dict[str, Any]]] = []
        self.global_broadcasts: List[Dict[str, Any]] = []

    async def broadcast(self, room_id: str, message: Dict[str, Any]) -> None:
        self.broadcasts.append((room_id, message))

    async def send_to_player(self, room_id: str, player_name: str, message: Dict[str, Any]) -> None:
        self.player_messages.append((room_id, player_name, message))

    async def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        self.global_broadcasts.append(message)

    def last_broadcast(self, event_type: Optional[str] = None) -> Optional[Tuple[str, Dict[str, Any]]]:
        for item in reversed(self.broadcasts):
            if event_type is None or item[1].get("type") == event_type:
                return item
        return None
