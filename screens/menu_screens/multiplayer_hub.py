import pygame
from gameState import GameState
from ui_elements import Button
import data.constants as c
from map_logic.rendering.font_manager import fonts

class Multiplayer_Hub(GameState):
    def __init__(self):
        super().__init__()
        self.bg_color = (10, 10, 40)
        self.elements = [
            Button("centered", 250, "medium", "green", "Host Game", self.host_game),
            Button("centered", 350, "medium", "blue", "Join Game", self.join_game),
            Button("centered", 450, "medium", "red", "Back", self.go_back)
        ]

    def host_game(self):
        self.next_state = "MULTIPLAYER_HOST"
        self.done = True

    def join_game(self):
        self.next_state = "MULTIPLAYER_JOIN"
        self.done = True

    def go_back(self):
        self.next_state = "MENU"
        self.done = True

    def draw(self, surface):
        surface.fill(self.bg_color)
        title_text = "Asynchronous Multiplayer"
        font = fonts.get("heading1")
        w = font.size(title_text)[0]
        fonts.draw_text_with_shadow(surface, title_text, c.SCREEN_WIDTH // 2 - w // 2, 100, "heading1", (255, 255, 255))
        super().draw(surface)
