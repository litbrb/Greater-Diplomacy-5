import os
from gameState import GameState
from ui_elements import Button
import data.constants as c

class Scenario_Settings(GameState):
    def __init__(self):
        super().__init__()
        self.bg_color = (80, 20, 60)
        self.selected_save_path = None
        self.refresh_maps()

    def refresh_maps(self):
        self.elements = [
            Button(20, 20, "small", "red", "Back", self.exit_to_menu),
        ]

    def exit_to_menu(self):
        self.next_state = "NEW_GAME"
        self.done = True

    def handle_back_key(self):
        self.exit_to_menu()