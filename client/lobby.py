import pygame

def lobby_screen(screen, on_join_callback):
    pygame.font.init()
    font = pygame.font.SysFont("Arial", 28)

    input_box_room = pygame.Rect(100, 150, 400, 40)
    input_box_name = pygame.Rect(100, 250, 400, 40)
    join_btn = pygame.Rect(100, 350, 200, 50)

    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')

    active_box = None
    text_room = ''
    text_name = ''

    running = True
    while running:
        screen.fill((240, 240, 240))

        title = font.render("Join a Room", True, (0, 0, 0))
        screen.blit(title, (100, 50))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box_room.collidepoint(event.pos):
                    active_box = 'room'
                elif input_box_name.collidepoint(event.pos):
                    active_box = 'name'
                elif join_btn.collidepoint(event.pos) and text_room and text_name:
                    on_join_callback(text_room, text_name)
                    running = False
            elif event.type == pygame.KEYDOWN:
                if active_box == 'room':
                    if event.key == pygame.K_BACKSPACE:
                        text_room = text_room[:-1]
                    else:
                        text_room += event.unicode
                elif active_box == 'name':
                    if event.key == pygame.K_BACKSPACE:
                        text_name = text_name[:-1]
                    else:
                        text_name += event.unicode

        pygame.draw.rect(screen, color_active if active_box == 'room' else color_inactive, input_box_room)
        pygame.draw.rect(screen, color_active if active_box == 'name' else color_inactive, input_box_name)
        pygame.draw.rect(screen, pygame.Color('green'), join_btn)

        screen.blit(font.render("Room ID:", True, (0,0,0)), (100, 120))
        screen.blit(font.render(text_room, True, (0,0,0)), (input_box_room.x+5, input_box_room.y+5))

        screen.blit(font.render("Your Name:", True, (0,0,0)), (100, 220))
        screen.blit(font.render(text_name, True, (0,0,0)), (input_box_name.x+5, input_box_name.y+5))

        screen.blit(font.render("Join", True, (255,255,255)), (join_btn.x + 50, join_btn.y + 10))

        pygame.display.flip()
