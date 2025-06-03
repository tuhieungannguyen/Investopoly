import pygame
from client.client_socket import ClientSocket
from client.client_handler import ClientHandler
from client.state_manager import StateManager
from client.host_dashboard import HostDashboard
from client.lobby import lobby_screen
from mainapi import main_loop

def start_game(room_id, player_name):
    # Khởi tạo socket & state
    state = StateManager()
    handler = ClientHandler(state)
    socket = ClientSocket(room_id, player_name, on_message_callback=handler.handle)
    socket.connect()
    socket.send_action("join", {"name": player_name})  # gửi tên vào server
    # chuyển sang màn hình game (board)
    main_loop(socket, state)

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("Monopoly Game")
    state = StateManager()
    lobby_screen(screen, start_game)

def host_screen(screen, state_manager):
    dashboard = HostDashboard(screen, state_manager, start_game_callback=start_game)
    dashboard.loop()
