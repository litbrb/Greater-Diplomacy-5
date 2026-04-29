import pygame
import ui_elements
from gameState import GameState
from data.io import keybind_io
import data.constants as c
from ui import buttons
from map_logic.rendering.font_manager import fonts

class Settings(GameState):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.bg_color = (40, 40, 40)
        self.bg_image_path = c.SETTINGS_BG_FILE # Hook up the new background here!
        self.return_state = "MENU"
        
        self.volume = self.controller.volume
        self.num_players = getattr(self.controller, 'num_players', 1)
        self.ai_mode = getattr(self.controller, 'ai_mode', 'GEMINI')
        self.ai_immersion_level = getattr(self.controller, 'ai_immersion_level', 'FULL')
        self.ai_modes = ["OFF", "GEMINI", "OLLAMA"]
        
        # Remember the last active AI mode so we can toggle back to it from OFF
        self.last_ai_mode = self.ai_mode if self.ai_mode != "OFF" else "GEMINI"
        
        self.fullscreen = False
        self.listening_for = None

        self.api_input_active = False
        self.api_key_text = getattr(self.controller, 'api_key', '')

        self.refresh_ui()

    def update(self):
        super().update()
        # Hide the player slider if we accessed settings mid-game
        if hasattr(self, 'player_slider'):
            self.player_slider.visible = (self.return_state != "MAP")

    def set_ai_mode(self, mode):
        self.ai_mode = mode
        self.controller.ai_mode = mode
        self.refresh_ui()

    def set_ai_immersion_level(self, level):
        self.ai_immersion_level = level
        self.controller.ai_immersion_level = level
        self.refresh_ui()

    def clear_api_key(self):
        self.api_key_text = ""
        self.controller.api_key = ""

    def refresh_ui(self):
        buttons.render_settings_buttons(self)

    # Replaces the old cycle toggle with a strict ON/OFF toggle
    def toggle_ai_enabled(self):
        if self.ai_mode == "OFF":
            self.set_ai_mode(self.last_ai_mode)
        else:
            self.last_ai_mode = self.ai_mode
            self.set_ai_mode("OFF")

    def start_listening(self, action):
        self.listening_for = action
        self.refresh_ui()

    def reset_defaults(self):
        default_keys = {"BACK": pygame.K_ESCAPE, "ORDERS": pygame.K_q}
        self.controller.keybinds = default_keys
        # Safely fetch api_key and immersion to ensure we don't accidentally wipe them
        api_key = getattr(self.controller, 'api_key', '')
        immersion = getattr(self.controller, 'ai_immersion_level', 'FULL')
        keybind_io.save_settings(default_keys, self.volume, self.num_players, self.ai_mode, api_key, immersion)
        self.refresh_ui()
        
    def handle_events(self, events):
        # Override to catch clicks on the API box before the elements get them
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Only check for API box collision if Gemini is currently active
                if self.ai_mode == "GEMINI":
                    mx, my = event.pos
                    api_rect = pygame.Rect(c.SETTINGS_API_BOX_X, c.SETTINGS_API_BOX_Y, c.SETTINGS_API_BOX_W, c.SETTINGS_API_BOX_H)
                    if api_rect.collidepoint(mx, my):
                        self.api_input_active = True
                    else:
                        self.api_input_active = False
                else:
                    self.api_input_active = False

            # Pass down to elements
            for el in self.elements:
                el.handle_event(event)

            self.additional_events(event)

    def additional_events(self, event):
        if self.listening_for and event.type == pygame.KEYDOWN:
            self.controller.keybinds[self.listening_for] = event.key
            keybind_io.save_settings(self.controller.keybinds, self.volume, self.num_players, self.ai_mode, getattr(self.controller, 'api_key', ''), getattr(self.controller, 'ai_immersion_level', 'FULL'))
            self.listening_for = None
            self.refresh_ui()

        # Only process keyboard input for the API box if Gemini is active
        elif getattr(self, "api_input_active", False) and self.ai_mode == "GEMINI":
            self.api_key_text, status = ui_elements.process_text_input(
                event, self.api_key_text, max_length=150
            )
            self.controller.api_key = self.api_key_text.strip()

    def additional_draw(self, surface):
        # Draw API Box ONLY if Gemini is active
        if self.ai_mode == "GEMINI":
            font = fonts.get("normal")

            label_surf = font.render("Gemini API Key (Required for Gemini Mode):", True, (200, 200, 200))
            surface.blit(label_surf, (c.SETTINGS_API_BOX_X, c.SETTINGS_API_BOX_Y - 25))

            api_rect = pygame.Rect(c.SETTINGS_API_BOX_X, c.SETTINGS_API_BOX_Y, c.SETTINGS_API_BOX_W, c.SETTINGS_API_BOX_H)
            bg_color = (60, 60, 80) if self.api_input_active else (20, 20, 30)
            pygame.draw.rect(surface, bg_color, api_rect)
            pygame.draw.rect(surface, (150, 150, 150), api_rect, 1)

            display_text = self.api_key_text
            if self.api_input_active:
                display_text += "|"

            txt_surf = font.render(display_text, True, (255, 255, 255))
            
            # Simple clipping in case the key exceeds the box visually
            surface.set_clip(api_rect.inflate(-10, -10))
            surface.blit(txt_surf, (api_rect.x + 5, api_rect.y + 10))
            surface.set_clip(None)

    def set_players(self, val):
        self.num_players = 1 + int(val * 7)
        self.controller.num_players = self.num_players
        # Update text via direct reference, not indexing
        if hasattr(self, 'player_slider'):
            self.player_slider.text = f"Players: {self.num_players}"

    def save_and_go_back(self):
        # Ensure we pass the api_key and immersion level when saving
        api_key_to_save = getattr(self.controller, 'api_key', '')
        immersion_to_save = getattr(self.controller, 'ai_immersion_level', 'FULL')
        keybind_io.save_settings(self.controller.keybinds, self.volume, self.num_players, self.ai_mode, api_key_to_save, immersion_to_save)
        
        self.next_state = getattr(self, 'return_state', 'MENU')
        self.done = True

    def handle_back_key(self):
        if not self.listening_for:
            self.save_and_go_back()
    
    def go_back(self):
        self.save_and_go_back()

    def toggle_full(self):
        self.fullscreen = not self.fullscreen
        pygame.display.toggle_fullscreen()

    def set_volume(self, val):
        self.volume = val
        self.controller.volume = val
        
        # Apply volume live as the slider moves
        if ui_elements.click_sound:
            ui_elements.click_sound.set_volume(val)
        if ui_elements.slider_sound:
            ui_elements.slider_sound.set_volume(val)