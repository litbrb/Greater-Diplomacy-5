import os
from gameState import GameState
from ui_elements import Button
import data.constants as c
from data import queries

class Scenario_Settings(GameState):
    return_screen = "NEW_GAME" # Track which screen to return to

    def __init__(self):
        super().__init__()
        self.bg_color = (80, 20, 60)
        # Load persistent settings instead of creating defaults
        self.settings = queries.get_scenario_settings()
        if not self.settings:
            self.settings = {
                "fog_of_war": c.DEFAULT_FOG_OF_WAR,
                "casus_belli_required": c.DEFAULT_CASUS_BELLI
            }
        self.refresh_ui()

    def refresh_ui(self):
        self.elements = [
            Button(20, 20, "small", "red", "Back", self.exit_to_menu),
        ]
        
        # Toggle Button - Fog of War
        fog_val = self.settings.get("fog_of_war", c.DEFAULT_FOG_OF_WAR)
        fog_color = "green" if fog_val else "red"
        fog_text = "Fog of War: ON" if fog_val else "Fog of War: OFF"
        
        self.elements.append(
            Button("centered", 200, "medium", fog_color, fog_text, self.toggle_fog)
        )

        # Toggle Button - Casus Belli Required
        cb_val = self.settings.get("casus_belli_required", c.DEFAULT_CASUS_BELLI)
        cb_color = "green" if cb_val else "red"
        cb_text = "Casus Belli Required: ON" if cb_val else "Casus Belli Required: OFF"

        self.elements.append(
            Button("centered", 280, "medium", cb_color, cb_text, self.toggle_casus_belli)
        )

        # Reset Defaults Button
        self.elements.append(
            Button("centered", 400, "medium", "grey", "Reset to Defaults", self.reset_defaults)
        )

    def toggle_fog(self):
        self.settings["fog_of_war"] = not self.settings.get("fog_of_war", c.DEFAULT_FOG_OF_WAR)
        # Save immediately to the cache/file
        queries.save_scenario_settings(self.settings)
        self.refresh_ui()

    def toggle_casus_belli(self):
        self.settings["casus_belli_required"] = not self.settings.get("casus_belli_required", c.DEFAULT_CASUS_BELLI)
        queries.save_scenario_settings(self.settings)
        self.refresh_ui()

    def reset_defaults(self):
        self.settings = {
            "fog_of_war": c.DEFAULT_FOG_OF_WAR,
            "casus_belli_required": c.DEFAULT_CASUS_BELLI
        }
        queries.save_scenario_settings(self.settings)
        self.refresh_ui()

    def exit_to_menu(self):
        self.next_state = self.__class__.return_screen
        self.done = True

    def handle_back_key(self):
        self.exit_to_menu()