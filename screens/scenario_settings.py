import os
from gameState import GameState
from ui_elements import Button
import data.constants as c
from map_logic.rendering.font_manager import fonts

class Scenario_Settings(GameState):
    def __init__(self, settings=None):
        super().__init__()
        self.bg_color = (80, 20, 60)
        # Initialize with passed settings or defaults
        self.settings = settings if settings is not None else {
            "fog_of_war": c.DEFAULT_FOG_OF_WAR
        }
        self.refresh_ui()

    def refresh_ui(self):
        self.elements = [
            Button(20, 20, "small", "red", "Back", self.exit_to_menu),
        ]
        
        # Toggle Button
        fog_color = "green" if self.settings.get("fog_of_war") else "red"
        fog_text = "Fog of War: ON" if self.settings.get("fog_of_war") else "Fog of War: OFF"
        
        self.elements.append(
            Button("centered", 200, "medium", fog_color, fog_text, self.toggle_fog)
        )

    def toggle_fog(self):
        self.settings["fog_of_war"] = not self.settings.get("fog_of_war", True)
        self.refresh_ui()

    def exit_to_menu(self):
        self.next_state = "NEW_GAME"
        self.done = True

    def handle_back_key(self):
        self.exit_to_menu()