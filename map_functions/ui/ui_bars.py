import pygame

def draw_ui_bars(map_screen, surface):
    # --- LAYER 4: UI BARS & HUD ---
    pygame.draw.rect(surface, (40, 40, 40), map_screen.top_bar_rect)
    pygame.draw.rect(surface, (40, 40, 40), map_screen.bot_bar_rect)
    
    if not map_screen.selection_mode and not getattr(map_screen, 'hide_raised_rect', False):
        pygame.draw.rect(surface, (160, 40, 40), map_screen.raised_rect)
        pygame.draw.rect(surface, (80, 80, 40), map_screen.ui_background_rect)