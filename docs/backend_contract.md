# Investopoly Backend Contract

Version: 0.1  
Status: current backend contract after stabilization pass  
Base HTTP URL: `http://localhost:8000`  
Base WebSocket URL: `ws://localhost:8000`

This document is the shared contract for the next web frontend. It describes the current FastAPI backend surface, including a few legacy endpoints that should be preserved until the web client fully replaces the Pygame client.

## Conventions

- Request and response bodies are JSON unless noted otherwise.
- Monetary values are numbers.
- `room_id` identifies one game room.
- `player_name` identifies a player inside a room.
- HTTP errors may be returned as either `{"error": string}` or FastAPI's default `{"detail": string}` depending on the endpoint.
- WebSocket messages sent by the server always include a string `type`.
- WebSocket messages sent by clients may use either action envelopes or REST endpoints. For the web frontend, prefer REST for commands and WebSocket for realtime updates.

## Shared Shapes

### Player

```json
{
  "player_name": "Alice",
  "current_position": 0,
  "cash": 2000,
  "stocks": {
    "SAB": 1
  },
  "estates": ["Real Estate 1"],
  "saving": 0,
  "net_worth": 2000,
  "round_played": 0,
  "pending_bonus": []
}
```

### Leaderboard Entry

```json
{
  "player": "Alice",
  "net_worth": 2000
}
```

### Tile

```json
{
  "name": "Real Estate 1",
  "owner": null,
  "value": 100
}
```

### Stock

```json
{
  "name": "SAB",
  "owner_list": ["Alice"],
  "industry": "A",
  "start_price": 200,
  "now_price": 204,
  "service_fee": 80,
  "position": 2,
  "available_units": 4,
  "max_per_player": 3
}
```

### Estate

```json
{
  "name": "Real Estate 1",
  "position": 1,
  "price": 100,
  "rent_price": 10,
  "owner_name": "Alice",
  "home_level": 0
}
```

## REST API

### Create Room

`POST /create`

Request:

```json
{
  "room_id": "room-123",
  "host_name": "Alice"
}
```

Success:

```json
{
  "message": "Room room-123 created by Alice"
}
```

Errors:

- `400 {"error": "Room already exists"}`

### Join Room

`POST /join`

Request:

```json
{
  "room_id": "room-123",
  "player_name": "Bob"
}
```

Success:

```json
{
  "message": "Bob joined room room-123"
}
```

Note: if the room does not exist, the current backend creates it with this player.

### Start Game

`POST /start`

Request:

```json
{
  "room_id": "room-123"
}
```

Success:

```json
{
  "message": "Game in room room-123 started"
}
```

Realtime side effect: broadcasts `game_started`.

### Get Room Status

`GET /status/{room_id}`

Success:

```json
{
  "round": 1,
  "current_player": "Alice",
  "players": {
    "Alice": {
      "player_name": "Alice",
      "current_position": 0,
      "cash": 2000,
      "stocks": {},
      "estates": [],
      "saving": 0,
      "net_worth": 2000,
      "round_played": 0,
      "pending_bonus": []
    }
  }
}
```

Errors:

- `404 {"error": "Room not found"}`

### Roll Dice

`POST /roll`

Request:

```json
{
  "room_id": "room-123",
  "player_name": "Alice"
}
```

Success:

```json
{
  "message": "Roll processed",
  "dice": 4,
  "tile": {
    "name": "Real Estate 2",
    "owner": null,
    "value": 200
  },
  "can_buy_estate": true,
  "can_buy_stock": false
}
```

Errors:

- `404 {"error": "Room not found"}`
- `403 {"error": "Not your turn"}`
- `403 {"error": "You have already rolled this round"}`

Realtime side effects may include: `leaderboard_update`, `player_rolled`, `update_positions`, plus tile-specific events.

### End Turn

`POST /end_turn`

Request:

```json
{
  "room_id": "room-123",
  "player_name": "Alice"
}
```

Success:

```json
{
  "message": "Turn ended"
}
```

Errors:

- `403 {"error": "Not your turn"}`

Realtime side effect: broadcasts `next_turn`. At round boundaries, backend may also broadcast `dividend_distributed`, `new_round_started`, or `game_ended`.

### Buy Estate

`POST /buy_estate`

Request:

```json
{
  "room_id": "room-123",
  "player_name": "Alice"
}
```

Success:

```json
{
  "success": true,
  "message": "Transaction Successful"
}
```

Failure:

```json
{
  "success": false,
  "message": "Not enough cash."
}
```

Realtime side effects: `estate_purchased`, `portfolio_update`.

### Buy Stock From Bank

`POST /buy_stock`

Request:

```json
{
  "room_id": "room-123",
  "player_name": "Alice",
  "amount": 1
}
```

Success:

```json
{
  "message": "Successfully bought 1 of SAB."
}
```

Errors:

- `404 {"detail": "Room or player not found."}`
- `400 {"detail": string}`

Realtime side effects: `stock_purchased`, `portfolio_update`.

### Submit Quiz Answer

`POST /quiz/answer`

Request:

```json
{
  "room_id": "room-123",
  "player_name": "Alice",
  "question_id": 1,
  "answer_index": 2
}
```

Success:

```json
{
  "correct": true
}
```

Realtime side effects: `quiz_result`, `portfolio_update`.

### Deposit Saving

Preferred endpoint for web:

`POST /api/saving/deposit`

Request:

```json
{
  "room_id": "room-123",
  "player_name": "Alice",
  "amount": 100
}
```

Success:

```json
{
  "success": true,
  "message": "Successfully deposited $100.00 to savings",
  "portfolio": {
    "player_name": "Alice",
    "current_position": 8,
    "cash": 1900,
    "stocks": {},
    "estates": [],
    "saving": 100,
    "net_worth": 2000,
    "round_played": 1,
    "pending_bonus": []
  }
}
```

Errors:

- `404 {"detail": "Room or player not found."}`
- `400 {"detail": string}`

Realtime side effects: `portfolio_update`, `saving_deposit_success`, `leaderboard_update`.

Legacy endpoint:

`POST /saving`

Accepts the same body and returns:

```json
{
  "message": "Successfully deposited $100.00 to savings"
}
```

### Withdraw Saving

`POST /api/saving/withdraw`

Request:

```json
{
  "room_id": "room-123",
  "player_name": "Alice"
}
```

Success:

```json
{
  "success": true,
  "message": "Withdrawn $104.0 (Interest: $4.0)",
  "amount": 104,
  "interest": 4,
  "portfolio": {}
}
```

Errors:

- `400 {"detail": "No savings to withdraw."}`

Realtime side effects: `portfolio_update`, `saving_withdraw_success`, `leaderboard_update`.

### List Stock For Sale

Preferred endpoint:

`POST /api/stock/list_for_sale`

Legacy alias:

`POST /stock/list`

Request:

```json
{
  "room_id": "room-123",
  "seller": "Alice",
  "stock": "SAB",
  "quantity": 1,
  "price_per_unit": 250
}
```

Success:

```json
{
  "success": true,
  "message": "Stock listed for sale."
}
```

Realtime side effect: `stock_for_sale`.

### Buy Stock From Player

`POST /api/stock/buy_from_player`

Request:

```json
{
  "room_id": "room-123",
  "buyer": "Bob",
  "seller": "Alice",
  "stock": "SAB",
  "quantity": 1,
  "price_per_unit": 250
}
```

Success:

```json
{
  "success": true,
  "message": "Stock purchase successful"
}
```

Realtime side effects: `stock_sold`, `portfolio_update`.

### List Estate For Sale

`POST /api/estate/list_for_sale`

Request:

```json
{
  "room_id": "room-123",
  "seller": "Alice",
  "estate": "Real Estate 1",
  "price": 300
}
```

Success:

```json
{
  "success": true,
  "message": "Estate listed for sale."
}
```

Realtime side effect: `estate_for_sale`.

### Offer Estate

`POST /api/estate/offer`

Request:

```json
{
  "room_id": "room-123",
  "buyer": "Bob",
  "estate_name": "Real Estate 1",
  "offer_price": 300
}
```

Success:

```json
{
  "success": true,
  "message": "Offer sent to seller."
}
```

Realtime side effect: `estate_offer_received`.

### Accept Estate Offer

`POST /api/estate/accept_offer`

Request:

```json
{
  "room_id": "room-123",
  "seller": "Alice",
  "estate_name": "Real Estate 1",
  "chosen_buyer": "Bob",
  "price": 300
}
```

Success:

```json
{
  "success": true,
  "message": "Ban da mua Real Estate 1 voi gia $300"
}
```

Realtime side effects: `estate_sold`, `portfolio_update`.

### End Game

`POST /end`

Request:

```json
{
  "room_id": "room-123"
}
```

Success:

```json
{
  "message": "Game ended",
  "results": {
    "leaderboard": [
      {
        "player": "Alice",
        "net_worth": 2300,
        "cash": 2000,
        "saving": 0,
        "stock_value": 200,
        "estate_count": 1
      }
    ],
    "summary": []
  }
}
```

Realtime side effect: `game_ended`.

### Admin And Debug

`GET /debug/print_state/{room_id}`

Returns:

```json
{
  "room_id": "room-123",
  "state": "debug text"
}
```

`GET /admin/list_rooms`

Returns:

```json
{
  "rooms": [
    {
      "room_id": "room-123",
      "players": ["Alice", "Bob"],
      "player_count": 2
    }
  ]
}
```

`POST /admin/reset_room/{room_id}`

Returns:

```json
{
  "message": "Room room-123 has been reset."
}
```

Realtime side effect: `room_reset`.

`POST /admin/reset_all_rooms`

Returns:

```json
{
  "message": "All rooms have been reset."
}
```

Realtime side effect: `server_reset`.

## WebSocket API

### Connect

`GET ws://localhost:8000/ws/{room_id}/{player_name}`

On connect, backend creates the room if needed or adds the player to an existing room. It then sends `player_joined` to the connecting player and all other players in that room.

### Client To Server Messages

The current backend accepts these action messages:

#### Broadcast Raw Message

```json
{
  "action": "broadcast",
  "type": "custom_event",
  "payload": {}
}
```

The backend broadcasts the entire message to the room.

#### Notify One Player

```json
{
  "action": "notify",
  "target": "Alice",
  "type": "custom_event",
  "payload": {}
}
```

The backend sends the entire message to `target`.

#### Estate Offer Legacy Action

```json
{
  "action": "estate_offer",
  "room_id": "room-123",
  "buyer": "Bob",
  "estate": "Real Estate 1",
  "price": 300
}
```

Prefer `POST /api/estate/offer` for the web frontend.

### Server To Client Events

#### `player_joined`

Sent on WebSocket connect and when another player joins.

```json
{
  "type": "player_joined",
  "player": "Alice",
  "players": [
    {
      "player_name": "Alice",
      "current_position": 0
    }
  ],
  "portfolio": {},
  "leaderboard": [
    {
      "player": "Alice",
      "net_worth": 2000
    }
  ]
}
```

#### `game_started`

```json
{
  "type": "game_started",
  "message": "Game has started!",
  "round": 1,
  "current_player": "Alice"
}
```

#### `next_turn`

```json
{
  "type": "next_turn",
  "round": 1,
  "current_player": "Bob",
  "message": "It's Bob's turn"
}
```

#### `new_round_started`

```json
{
  "type": "new_round_started",
  "message": "Round 2 has started!",
  "current_round": 2,
  "remaining_rounds": 13,
  "current_player": "Alice"
}
```

#### `player_rolled`

```json
{
  "type": "player_rolled",
  "player": "Alice",
  "dice": 4,
  "tile": {
    "name": "Real Estate 2",
    "owner": null,
    "value": 200
  },
  "message": "Player Alice rolled a 4",
  "can_buy_estate": true,
  "can_buy_stock": false
}
```

#### `update_positions`

```json
{
  "type": "update_positions",
  "players": [
    {
      "player_name": "Alice",
      "current_position": 4
    }
  ]
}
```

#### `leaderboard_update`

```json
{
  "type": "leaderboard_update",
  "leaderboard": [
    {
      "player": "Alice",
      "net_worth": 2100
    }
  ]
}
```

#### `portfolio_update`

```json
{
  "type": "portfolio_update",
  "portfolio": {}
}
```

#### `passed_go`

```json
{
  "type": "passed_go",
  "message": "Alice passed GO and received $200",
  "player": "Alice",
  "amount": 200
}
```

#### `estate_purchased`

```json
{
  "type": "estate_purchased",
  "player": "Alice",
  "message": "Alice has purchased Real Estate 1 for $100.",
  "tile": "Real Estate 1",
  "price": 100,
  "leaderboard": []
}
```

#### `estate_rent_paid`

```json
{
  "type": "estate_rent_paid",
  "message": "Bob paid $10 rent to Alice for landing on Real Estate 1.",
  "payer": "Bob",
  "owner": "Alice",
  "amount": 10,
  "tile": "Real Estate 1"
}
```

#### `estate_for_sale`

```json
{
  "type": "estate_for_sale",
  "message": "Alice is selling Real Estate 1 for $300",
  "seller": "Alice",
  "estate": "Real Estate 1",
  "price": 300
}
```

#### `estate_offer_received`

```json
{
  "type": "estate_offer_received",
  "estate": "Real Estate 1",
  "offers": [
    {
      "buyer": "Bob",
      "price": 300
    }
  ]
}
```

#### `estate_sold`

```json
{
  "type": "estate_sold",
  "message": "Alice sold Real Estate 1 to Bob for $300",
  "buyer": "Bob",
  "seller": "Alice",
  "estate": "Real Estate 1",
  "price": 300
}
```

#### `stock_purchased`

```json
{
  "type": "stock_purchased",
  "message": "Alice bought 1 of SAB at $200 each.",
  "stock": {},
  "player": "Alice"
}
```

#### `stock_service_fee`

```json
{
  "type": "stock_service_fee",
  "message": "Alice paid $80 service fee for landing on SAB stock tile.",
  "player": "Alice",
  "stock": "SAB",
  "amount": 80
}
```

#### `dividend_distributed`

```json
{
  "type": "dividend_distributed",
  "message": "Stock SAB: EPS = $16.00, Dividend = $4.80"
}
```

#### `stock_for_sale`

```json
{
  "type": "stock_for_sale",
  "message": "Alice is selling 1 shares of SAB at $250/unit",
  "stock": "SAB",
  "seller": "Alice",
  "quantity": 1,
  "price_per_unit": 250
}
```

#### `stock_sold`

```json
{
  "type": "stock_sold",
  "message": "Alice sold 1 of SAB to Bob at $250/unit",
  "stock": "SAB",
  "buyer": "Bob",
  "seller": "Alice",
  "quantity": 1,
  "price_per_unit": 250
}
```

#### `shock_event`

```json
{
  "type": "shock_event",
  "message": "Shock Event: Global Pandemic - ...",
  "stocks": [],
  "updated_estates": []
}
```

#### `chance_event`

```json
{
  "type": "chance_event",
  "message": "Alice triggered Chance: Win lottery +$600",
  "player": "Alice",
  "event": {
    "name": "Win lottery +$600",
    "type": "plus",
    "amount": 600
  }
}
```

#### `quiz_start`

```json
{
  "type": "quiz_start",
  "player": "Alice",
  "message": "Alice is attempting a quiz!"
}
```

#### `quiz_question`

```json
{
  "type": "quiz_question",
  "question_id": 1,
  "question": "Question text",
  "options": ["A", "B", "C", "D"]
}
```

#### `quiz_result`

```json
{
  "type": "quiz_result",
  "player": "Alice",
  "correct": true,
  "message": "Alice answered quiz correctly and earned $50!"
}
```

#### `saving_prompt`

```json
{
  "type": "saving_prompt",
  "message": "You landed on the Saving tile. How much do you want to save?",
  "max_amount": 1900,
  "room_id": "room-123",
  "player_name": "Alice"
}
```

#### `saving_deposit_success`

```json
{
  "type": "saving_deposit_success",
  "message": "Alice deposited $100 to savings",
  "player": "Alice",
  "amount": 100
}
```

#### `saving_withdraw_success`

```json
{
  "type": "saving_withdraw_success",
  "message": "Withdrawn $104.0 (Interest: $4.0)",
  "player": "Alice",
  "amount": 104,
  "interest": 4
}
```

#### `saving_matured`

```json
{
  "type": "saving_matured",
  "message": "Alice received $100 + $12 interest from savings.",
  "player": "Alice",
  "amount": 100,
  "interest": 12
}
```

#### `tile_penalty`

```json
{
  "type": "tile_penalty",
  "message": "Alice landed on penalty tile and lost $100.",
  "player": "Alice",
  "amount": 100
}
```

#### `game_ended`

There are currently two shapes depending on how the game ends.

Manual `/end`:

```json
{
  "type": "game_ended",
  "leaderboard": [],
  "summary": []
}
```

Automatic round-limit end:

```json
{
  "type": "game_ended",
  "message": "Game has ended after 15 rounds!",
  "final_results": {
    "leaderboard": [],
    "summary": []
  },
  "winner": "Alice",
  "total_rounds": 15
}
```

Frontend should support both until the backend event is normalized.

#### `final_portfolio`

```json
{
  "type": "final_portfolio",
  "portfolio": {},
  "rank": 1
}
```

#### `server_reset`

```json
{
  "type": "server_reset",
  "message": "All rooms have been reset."
}
```

#### `room_reset`

```json
{
  "type": "room_reset",
  "message": "Room room-123 has been reset."
}
```

## Frontend Recommendations

- Use `POST /create`, then connect WebSocket to `/ws/{room_id}/{player_name}`.
- Use REST endpoints for commands: start, roll, buy, sell, saving, quiz, end turn.
- Treat WebSocket events as the source for UI updates and notifications.
- On initial page load or reconnect, call `GET /status/{room_id}` to hydrate state.
- Prefer `/api/saving/deposit` over `/saving`.
- Prefer `/api/stock/list_for_sale` over `/stock/list`.
- Support both `game_ended` shapes until backend normalization.

## Known Contract Gaps To Fix Later

- Error responses are not uniform yet.
- Some response messages contain legacy mojibake text from old source encoding.
- `game_ended` has two different WebSocket shapes.
- Several WebSocket payloads use raw `portfolio: {}` in this document because the backend sends full `Player` objects.
- WebSocket client command handling is still legacy. The web client should prefer REST commands first.
