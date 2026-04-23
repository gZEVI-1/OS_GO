# Network PvP API Documentation

## WebSocket Protocol

### Connection Flow

```
Client                                          Server
  | ---- {type:"connect", username:"Alice"} ----> |
  | <--- {type:"connected", player_id:"..."} --- |
  | ---- {type:"create_room", ...} ------------> |
  | <--- {type:"room_created", ...} ------------ |
  | ---- {type:"ready"} -----------------------> |
  | <--- {type:"game_start", ...} -------------- |
  | ---- {type:"make_move", x:3, y:4} ---------> |
  | <--- {type:"move_made", x:3, y:4} ---------- |
```

### Message Reference

#### Client → Server

##### `connect`
Initial connection message.
```json
{
  "type": "connect",
  "token": "jwt_token_here",
  "username": "PlayerName"
}
```

##### `create_room`
Create new game room.
```json
{
  "type": "create_room",
  "name": "My Room",
  "settings": {
    "board_size": 19,
    "rules": "chinese",
    "komi": 7.5,
    "handicap": 0,
    "time_limit": null,
    "byo_yomi": null
  },
  "password": "optional_password"
}
```

##### `join_room`
Join existing room.
```json
{
  "type": "join_room",
  "room_id": "abc123",
  "password": "optional_password"
}
```

##### `ready`
Signal readiness to start.
```json
{
  "type": "ready"
}
```

##### `make_move`
Place a stone.
```json
{
  "type": "make_move",
  "x": 3,
  "y": 4,
  "color": "black"
}
```

##### `pass`
Pass turn.
```json
{
  "type": "pass"
}
```

##### `resign`
Resign game.
```json
{
  "type": "resign"
}
```

##### `chat`
Send chat message.
```json
{
  "type": "chat",
  "text": "Hello!"
}
```

##### `sync_request`
Request full state sync (for reconnection).
```json
{
  "type": "sync_request"
}
```

#### Server → Client

##### `connected`
Connection confirmed.
```json
{
  "type": "connected",
  "player_id": "uuid",
  "username": "PlayerName"
}
```

##### `room_created`
Room creation confirmed.
```json
{
  "type": "room_created",
  "room": {
    "id": "abc123",
    "name": "My Room",
    "host": {...},
    "settings": {...},
    "players": [...],
    "status": "waiting",
    "password_protected": false
  },
  "your_color": "black"
}
```

##### `room_joined`
Room join confirmed.
```json
{
  "type": "room_joined",
  "room": {...},
  "your_color": "white"
}
```

##### `player_joined`
Another player joined.
```json
{
  "type": "player_joined",
  "player": {
    "id": "uuid",
    "username": "Bob",
    "rating": 0,
    "color": "white",
    "ready": false
  }
}
```

##### `game_start`
Game begins.
```json
{
  "type": "game_start",
  "game_state": {
    "board_size": 19,
    "moves": [],
    "current_turn": "black",
    "pass_count": 0,
    "captured_black": 0,
    "captured_white": 0
  },
  "settings": {
    "board_size": 19,
    "rules": "chinese",
    "komi": 7.5
  }
}
```

##### `move_made`
Move validated and applied.
```json
{
  "type": "move_made",
  "x": 3,
  "y": 4,
  "color": "black",
  "move_number": 1,
  "captured": [[5,4], [5,5]]
}
```

##### `game_over`
Game ended.
```json
{
  "type": "game_over",
  "winner": "black",
  "reason": "resignation",
  "score_black": null,
  "score_white": null
}
```

##### `error`
Error occurred.
```json
{
  "type": "error",
  "code": "INVALID_MOVE",
  "description": "Position already occupied"
}
```

##### `sync_state`
Full state for reconnection.
```json
{
  "type": "sync_state",
  "room": {...},
  "game_state": {...},
  "chat_history": [...]
}
```

## HTTP Endpoints

### GET /
Health check.

Response:
```json
{
  "status": "online",
  "service": "OS-GO Network Server",
  "version": "1.0.0",
  "rooms": 5,
  "players_online": 10
}
```

### GET /rooms
List available rooms.

Response:
```json
{
  "rooms": [
    {
      "id": "abc123",
      "name": "My Room",
      "host": {...},
      "settings": {...},
      "players": [...],
      "status": "waiting",
      "password_protected": false
    }
  ]
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `AUTH_REQUIRED` | First message must be connect |
| `CREATE_FAILED` | Room creation failed |
| `JOIN_FAILED` | Room join failed |
| `NOT_IN_ROOM` | Player not in a room |
| `NO_GAME` | No active game |
| `WRONG_TURN` | Not player's turn |
| `INVALID_MOVE` | Move validation failed |
| `UNKNOWN_TYPE` | Unknown message type |
| `MISSING_ROOM_ID` | Room ID not provided |
| `ROOM_FULL` | Room has maximum players |
| `GAME_IN_PROGRESS` | Cannot join running game |
| `INVALID_PASSWORD` | Wrong room password |

## Integration Guide

### Console Mode
```python
from console_pvp_network import ConsoleNetworkPvP
import asyncio

async def main():
    game = ConsoleNetworkPvP("ws://server:8765/ws")
    await game.run()

asyncio.run(main())
```

### GUI Mode (PySide6)
```python
from PySide6.QtCore import QObject, Signal
from console_pvp_network import NetworkPvPGame, NetworkGameCallbacks

class GameBridge(QObject):
    moveMade = Signal(dict)
    
    def __init__(self):
        self.game = NetworkPvPGame()
        self.game.callbacks = NetworkGameCallbacks(
            on_move_made=self.moveMade.emit
        )
```

### Custom Client
```python
from client import NetworkClient, ClientConfig

config = ClientConfig(server_url="ws://server:8765/ws", username="Player")
client = NetworkClient(config)
await client.connect()
await client.run()
```
