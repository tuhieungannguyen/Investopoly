import websocket
import threading
import json

class ClientSocket:
    def __init__(self, room_id, player_id, on_message_callback=None):
        self.room_id = room_id
        self.player_id = player_id
        self.ws = None
        self.on_message_callback = on_message_callback

    def connect(self):
        url = f"ws://localhost:8000/ws/{self.room_id}/{self.player_id}"
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        threading.Thread(target=self.ws.run_forever, daemon=True).start()

    def on_open(self, wsapp):
        print(f"[WS] Connected as {self.player_id} to room {self.room_id}")

    def on_message(self, wsapp, message):
        print("[WS] Received:", message)
        data = json.loads(message)
        if self.on_message_callback:
            self.on_message_callback(data)

    def on_error(self, wsapp, error):
        print("[WS] Error:", error)

    def on_close(self, wsapp, close_status_code, close_msg):
        print("[WS] Connection closed")

    def send_action(self, action, payload=None):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            msg = {"action": action}
            if payload:
                msg["payload"] = payload
            self.ws.send(json.dumps(msg))
        else:
            print("[WS] Not connected!")
