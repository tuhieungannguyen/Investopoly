import asyncio
import unittest

from server.manager.event_sink import RecordingEventSink
from server.manager.game_state import GameState


class GameStateTests(unittest.TestCase):
    def setUp(self):
        self.sink = RecordingEventSink()
        self.state = GameState(self.sink)
        self.state.init_room("room", ["Alice", "Bob"])

    def test_init_room_creates_independent_player_state(self):
        alice = self.state.players["room"]["Alice"]
        bob = self.state.players["room"]["Bob"]

        alice.stocks["SAB"] = 1
        alice.estates.append("Real Estate 1")

        self.assertEqual(bob.stocks, {})
        self.assertEqual(bob.estates, [])
        self.assertEqual(self.state.managers["room"].current_player, "Alice")

    def test_buy_estate_runs_without_websocket_manager(self):
        self.state.players["room"]["Alice"].current_position = 1

        result = self.state.buy_estate("room", "Alice")

        self.assertTrue(result["success"])
        self.assertEqual(self.state.players["room"]["Alice"].cash, 1900)
        self.assertEqual(self.state.estates["room"][0].owner_name, "Alice")
        self.assertIsNotNone(self.sink.last_broadcast("estate_purchased"))

    def test_buy_stock_runs_without_event_loop(self):
        self.state.players["room"]["Alice"].current_position = 2

        result = self.state.buy_stock("room", "Alice", 1)

        self.assertTrue(result["success"])
        self.assertEqual(self.state.players["room"]["Alice"].stocks["SAB"], 1)
        self.assertEqual(self.state.players["room"]["Alice"].cash, 1800)
        self.assertEqual(self.state.stocks["room"]["SAB"].available_units, 4)
        self.assertIsNotNone(self.sink.last_broadcast("stock_purchased"))

    def test_move_player_emits_events_through_sink(self):
        self.state.players["room"]["Alice"].current_position = 19

        tile = asyncio.run(self.state.move_player("room", "Alice", 1))

        self.assertEqual(tile["name"], "GO")
        self.assertEqual(self.state.players["room"]["Alice"].current_position, 0)
        self.assertEqual(self.state.players["room"]["Alice"].cash, 2200)
        self.assertIsNotNone(self.sink.last_broadcast("passed_go"))

    def test_next_turn_can_complete_round_without_event_loop(self):
        self.state.start_game("room")

        self.state.next_turn("room")
        self.assertEqual(self.state.managers["room"].current_player, "Bob")
        self.assertEqual(self.state.managers["room"].current_round, 1)

        self.state.next_turn("room")
        self.assertEqual(self.state.managers["room"].current_player, "Alice")
        self.assertEqual(self.state.managers["room"].current_round, 2)
        self.assertIsNotNone(self.sink.last_broadcast("new_round_started"))


if __name__ == "__main__":
    unittest.main()
