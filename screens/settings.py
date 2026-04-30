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
        self.bg_image_path = c.SETTINGS_BG_FILE 
        self.return_state = "MENU"
        
        self.volume = self.controller.volume
        self.num_players = getattr(self.controller, 'num_players', 1)
        self.ai_mode = getattr(self.controller, 'ai_mode', 'GEMINI')
        self.ai_immersion_level = getattr(self.controller, 'ai_immersion_level', 'FULL')
        self.ai_modes = ["OFF", "GEMINI", "OLLAMA", "CHATGPT", "CLAUDE"]
        
        self.last_ai_mode = self.ai_mode if self.ai_mode != "OFF" else "GEMINI"
        
        self.fullscreen = False
        self.listening_for = None

        self.api_input_active = False
        self.api_key_text = getattr(self.controller, 'api_key', '')

        self.ollama_input_active = False
        self.ollama_model_text = getattr(self.controller, 'ollama_model', 'llama3')

        self.chatgpt_input_active = False
        self.chatgpt_api_key_text = getattr(self.controller, 'chatgpt_api_key', '')

        self.claude_input_active = False
        self.claude_api_key_text = getattr(self.controller, 'claude_api_key', '')

        self.refresh_ui()

    def update(self):
        super().update()
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

    def clear_ollama_model(self):
        self.ollama_model_text = ""
        self.controller.ollama_model = ""

    def clear_chatgpt_api_key(self):
        self.chatgpt_api_key_text = ""
        self.controller.chatgpt_api_key = ""

    def clear_claude_api_key(self):
        self.claude_api_key_text = ""
        self.controller.claude_api_key = ""

    def refresh_ui(self):
        buttons.render_settings_buttons(self)

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
        
        api_key = getattr(self.controller, 'api_key', '')
        chatgpt_key = getattr(self.controller, 'chatgpt_api_key', '')
        claude_key = getattr(self.controller, 'claude_api_key', '')
        immersion = getattr(self.controller, 'ai_immersion_level', 'FULL')
        ollama = getattr(self.controller, 'ollama_model', 'llama3')
        
        keybind_io.save_settings(default_keys, self.volume, self.num_players, self.ai_mode, api_key, chatgpt_key, claude_key, immersion, ollama)
        self.refresh_ui()
        
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                
                # Input Box Handling
                if self.ai_mode == "GEMINI":
                    api_rect = pygame.Rect(c.SETTINGS_API_BOX_X, c.SETTINGS_API_BOX_Y, c.SETTINGS_API_BOX_W, c.SETTINGS_API_BOX_H)
                    self.api_input_active = api_rect.collidepoint(mx, my)
                    self.ollama_input_active = self.chatgpt_input_active = self.claude_input_active = False
                elif self.ai_mode == "OLLAMA":
                    ollama_rect = pygame.Rect(c.SETTINGS_OLLAMA_BOX_X, c.SETTINGS_OLLAMA_BOX_Y, c.SETTINGS_OLLAMA_BOX_W, c.SETTINGS_OLLAMA_BOX_H)
                    self.ollama_input_active = ollama_rect.collidepoint(mx, my)
                    self.api_input_active = self.chatgpt_input_active = self.claude_input_active = False
                elif self.ai_mode == "CHATGPT":
                    chatgpt_rect = pygame.Rect(c.SETTINGS_CHATGPT_BOX_X, c.SETTINGS_CHATGPT_BOX_Y, c.SETTINGS_CHATGPT_BOX_W, c.SETTINGS_CHATGPT_BOX_H)
                    self.chatgpt_input_active = chatgpt_rect.collidepoint(mx, my)
                    self.api_input_active = self.ollama_input_active = self.claude_input_active = False
                elif self.ai_mode == "CLAUDE":
                    claude_rect = pygame.Rect(c.SETTINGS_CLAUDE_BOX_X, c.SETTINGS_CLAUDE_BOX_Y, c.SETTINGS_CLAUDE_BOX_W, c.SETTINGS_CLAUDE_BOX_H)
                    self.claude_input_active = claude_rect.collidepoint(mx, my)
                    self.api_input_active = self.ollama_input_active = self.chatgpt_input_active = False
                else:
                    self.api_input_active = self.ollama_input_active = self.chatgpt_input_active = self.claude_input_active = False

            for el in self.elements:
                el.handle_event(event)
            self.additional_events(event)

    def additional_events(self, event):
        if self.listening_for and event.type == pygame.KEYDOWN:
            self.controller.keybinds[self.listening_for] = event.key
            keybind_io.save_settings(self.controller.keybinds, self.volume, self.num_players, self.ai_mode, getattr(self.controller, 'api_key', ''), getattr(self.controller, 'chatgpt_api_key', ''), getattr(self.controller, 'claude_api_key', ''), getattr(self.controller, 'ai_immersion_level', 'FULL'), getattr(self.controller, 'ollama_model', 'llama3'))
            self.listening_for = None
            self.refresh_ui()

        elif getattr(self, "api_input_active", False) and self.ai_mode == "GEMINI":
            self.api_key_text, status = ui_elements.process_text_input(event, self.api_key_text, max_length=150)
            self.controller.api_key = self.api_key_text.strip()
            
        elif getattr(self, "ollama_input_active", False) and self.ai_mode == "OLLAMA":
            self.ollama_model_text, status = ui_elements.process_text_input(event, self.ollama_model_text, max_length=50)
            self.controller.ollama_model = self.ollama_model_text.strip()
            
        elif getattr(self, "chatgpt_input_active", False) and self.ai_mode == "CHATGPT":
            self.chatgpt_api_key_text, status = ui_elements.process_text_input(event, self.chatgpt_api_key_text, max_length=150)
            self.controller.chatgpt_api_key = self.chatgpt_api_key_text.strip()
            
        elif getattr(self, "claude_input_active", False) and self.ai_mode == "CLAUDE":
            self.claude_api_key_text, status = ui_elements.process_text_input(event, self.claude_api_key_text, max_length=150)
            self.controller.claude_api_key = self.claude_api_key_text.strip()

    def additional_draw(self, surface):
        font = fonts.get("normal")
        
        if self.ai_mode == "GEMINI":
            label_surf = font.render("Gemini API Key (Required for Gemini Mode):", True, (200, 200, 200))
            surface.blit(label_surf, (c.SETTINGS_API_BOX_X, c.SETTINGS_API_BOX_Y - 25))

            api_rect = pygame.Rect(c.SETTINGS_API_BOX_X, c.SETTINGS_API_BOX_Y, c.SETTINGS_API_BOX_W, c.SETTINGS_API_BOX_H)
            bg_color = (60, 60, 80) if self.api_input_active else (20, 20, 30)
            pygame.draw.rect(surface, bg_color, api_rect)
            pygame.draw.rect(surface, (150, 150, 150), api_rect, 1)

            display_text = self.api_key_text
            if self.api_input_active: display_text += "|"

            txt_surf = font.render(display_text, True, (255, 255, 255))
            surface.set_clip(api_rect.inflate(-10, -10))
            surface.blit(txt_surf, (api_rect.x + 5, api_rect.y + 10))
            surface.set_clip(None)
            
        elif self.ai_mode == "OLLAMA":
            label_surf = font.render("Ollama Model Name (e.g. llama3, phi3):", True, (200, 200, 200))
            surface.blit(label_surf, (c.SETTINGS_OLLAMA_BOX_X, c.SETTINGS_OLLAMA_BOX_Y - 25))

            ollama_rect = pygame.Rect(c.SETTINGS_OLLAMA_BOX_X, c.SETTINGS_OLLAMA_BOX_Y, c.SETTINGS_OLLAMA_BOX_W, c.SETTINGS_OLLAMA_BOX_H)
            bg_color = (60, 60, 80) if self.ollama_input_active else (20, 20, 30)
            pygame.draw.rect(surface, bg_color, ollama_rect)
            pygame.draw.rect(surface, (150, 150, 150), ollama_rect, 1)

            display_text = self.ollama_model_text
            if self.ollama_input_active: display_text += "|"

            txt_surf = font.render(display_text, True, (255, 255, 255))
            surface.set_clip(ollama_rect.inflate(-10, -10))
            surface.blit(txt_surf, (ollama_rect.x + 5, ollama_rect.y + 10))
            surface.set_clip(None)
            
        elif self.ai_mode == "CHATGPT":
            label_surf = font.render("ChatGPT API Key:", True, (200, 200, 200))
            surface.blit(label_surf, (c.SETTINGS_CHATGPT_BOX_X, c.SETTINGS_CHATGPT_BOX_Y - 25))

            gpt_rect = pygame.Rect(c.SETTINGS_CHATGPT_BOX_X, c.SETTINGS_CHATGPT_BOX_Y, c.SETTINGS_CHATGPT_BOX_W, c.SETTINGS_CHATGPT_BOX_H)
            bg_color = (60, 60, 80) if self.chatgpt_input_active else (20, 20, 30)
            pygame.draw.rect(surface, bg_color, gpt_rect)
            pygame.draw.rect(surface, (150, 150, 150), gpt_rect, 1)

            display_text = self.chatgpt_api_key_text
            if self.chatgpt_input_active: display_text += "|"

            txt_surf = font.render(display_text, True, (255, 255, 255))
            surface.set_clip(gpt_rect.inflate(-10, -10))
            surface.blit(txt_surf, (gpt_rect.x + 5, gpt_rect.y + 10))
            surface.set_clip(None)
            
        elif self.ai_mode == "CLAUDE":
            label_surf = font.render("Claude API Key:", True, (200, 200, 200))
            surface.blit(label_surf, (c.SETTINGS_CLAUDE_BOX_X, c.SETTINGS_CLAUDE_BOX_Y - 25))

            claude_rect = pygame.Rect(c.SETTINGS_CLAUDE_BOX_X, c.SETTINGS_CLAUDE_BOX_Y, c.SETTINGS_CLAUDE_BOX_W, c.SETTINGS_CLAUDE_BOX_H)
            bg_color = (60, 60, 80) if self.claude_input_active else (20, 20, 30)
            pygame.draw.rect(surface, bg_color, claude_rect)
            pygame.draw.rect(surface, (150, 150, 150), claude_rect, 1)

            display_text = self.claude_api_key_text
            if self.claude_input_active: display_text += "|"

            txt_surf = font.render(display_text, True, (255, 255, 255))
            surface.set_clip(claude_rect.inflate(-10, -10))
            surface.blit(txt_surf, (claude_rect.x + 5, claude_rect.y + 10))
            surface.set_clip(None)

    def set_players(self, val):
        self.num_players = 1 + int(val * 7)
        self.controller.num_players = self.num_players
        if hasattr(self, 'player_slider'):
            self.player_slider.text = f"Players: {self.num_players}"

    def save_and_go_back(self):
        api_key_to_save = getattr(self.controller, 'api_key', '')
        chatgpt_to_save = getattr(self.controller, 'chatgpt_api_key', '')
        claude_to_save = getattr(self.controller, 'claude_api_key', '')
        immersion_to_save = getattr(self.controller, 'ai_immersion_level', 'FULL')
        ollama_to_save = getattr(self.controller, 'ollama_model', 'llama3')
        
        keybind_io.save_settings(self.controller.keybinds, self.volume, self.num_players, self.ai_mode, api_key_to_save, chatgpt_to_save, claude_to_save, immersion_to_save, ollama_to_save)
        
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
        if ui_elements.click_sound:
            ui_elements.click_sound.set_volume(val)
        if ui_elements.slider_sound:
            ui_elements.slider_sound.set_volume(val)