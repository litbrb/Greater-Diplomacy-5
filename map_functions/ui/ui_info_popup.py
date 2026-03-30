import pygame

info_rect = pygame.Rect(1380, 70, 210, 350) # Made slightly taller
recruit_btn_rect = pygame.Rect(1390, 370, 190, 40)

def draw_unit_info(self, surface):
    if not self.selected_province:
        return

    # Draw Panel
    pygame.draw.rect(surface, (30, 30, 50), info_rect)
    pygame.draw.rect(surface, (100, 100, 250), info_rect, 2)

    # --- Draw Units ---
    title = self.font.render("Active Garrison", True, (255, 255, 255))
    surface.blit(title, (info_rect.x + 10, info_rect.y + 10))

    units = self.selected_province.get("units", [])
    y_offset = info_rect.y + 40
    
    if not units:
        txt = self.small_font.render("(Empty)", True, (150, 150, 150))
        surface.blit(txt, (info_rect.x + 15, y_offset))
        y_offset += 25
    else:
        for i, unit_data in enumerate(units[:6]): # Cap at 6 to leave room for buildings
            u_name = unit_data["type"]
            u_owner_id = unit_data["owner"]
            
            # Resolve the owner's Display Name
            u_owner_display = self.nation_data.get(u_owner_id, {}).get("name", u_owner_id)
            
            display_text = f"- {u_name} ({u_owner_display})"
            txt = self.small_font.render(display_text, True, (200, 200, 200))
            surface.blit(txt, (info_rect.x + 15, y_offset))
            y_offset += 25

    # --- Draw Buildings ---
    y_offset += 10
    b_title = self.font.render("Buildings", True, (255, 255, 255))
    surface.blit(b_title, (info_rect.x + 10, y_offset))
    y_offset += 30
    
    buildings = self.selected_province.get("buildings", [])
    if not buildings:
        txt = self.small_font.render("(None)", True, (150, 150, 150))
        surface.blit(txt, (info_rect.x + 15, y_offset))
    else:
        for b in buildings[:6]:
            txt = self.small_font.render(f"- {b}", True, (200, 200, 200))
            surface.blit(txt, (info_rect.x + 15, y_offset))
            y_offset += 25