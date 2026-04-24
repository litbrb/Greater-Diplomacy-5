import pygame
from data.constants import UNPLAYABLE_NATIONS
from map_logic.rendering.font_manager import fonts

def draw_country_names(map_screen, surface):
    # --- LAYER 3.5: COUNTRY NAMES ---
    # Only show names on the Political map to avoid cluttering other modes
    # if map_screen.base_layer == "POLITICAL":
    # if map_screen.secondary_mode == "BLANK":
    if False: # ignore this for now
        
        # 1. Cache text surfaces once to save performance
        if not hasattr(map_screen, 'country_name_surfs'):
            map_screen.country_name_surfs = {}
            # Use your biggest font preset for maximum resolution before scaling down
            name_font = fonts.get("country_name_display") 
            for c_id, data in map_screen.nation_data.items():
                if c_id not in UNPLAYABLE_NATIONS:
                    disp = data.get("name", c_id).upper()
                    surf = name_font.render(disp, True, (255, 255, 255)).convert_alpha()
                    shadow = name_font.render(disp, True, (20, 20, 20)).convert_alpha()
                    map_screen.country_name_surfs[c_id] = (surf, shadow)

        # 2 & 3. Draw the names with DYNAMIC alpha
        if hasattr(map_screen, 'country_text_blobs'):
            import math
            
            drawn_countries = set()
            # Sort largest spatial spread to smallest so mainlands are always processed first!
            sorted_blobs = sorted(map_screen.country_text_blobs, key=lambda b: b["spread"], reverse=True)
            
            for blob in sorted_blobs:
                country = blob["owner"]
                
                # Skip small island groups ONLY IF the country already has a name on the map
                if blob["count"] <= 1 and country in drawn_countries:
                    continue

                # if blob["count"] <= 3:
                #     continue

                surf, shadow = map_screen.country_name_surfs.get(country, (None, None))
                if not surf: continue

                cx, cy = blob["cx"], blob["cy"]
                
                # Wrap logic for looped maps
                offsets = [0, -map_screen.map_w, map_screen.map_w] if map_screen.loop_map else [0]
                for offset in offsets:
                    sx = (cx + offset - map_screen.camera.pos.x) * map_screen.camera.zoom
                    sy = (cy - map_screen.camera.pos.y) * map_screen.camera.zoom + map_screen.top_ui_height

                    # Frustum Culling: Only draw if it's actually on the screen
                    if -200 < sx < surface.get_width() + 200 and 0 < sy < surface.get_height():
                        
                        # --- THE NEW SCALING LOGIC ---
                        scale_by_length = blob["length"] / surf.get_width()
                        scale_by_thickness = (blob["thickness"] * 0.8) / surf.get_height()
                        
                        land_scale = min(scale_by_length, scale_by_thickness)
                        land_scale = min(max(land_scale, 0.05), 1.0)
                        
                        # --- UNIVERSAL LINEAR FADE LOGIC ---
                        # Every country now fades at the exact same zoom levels.
                        # Tweak these two variables to your liking:
                        fade_start = 9.0   # Zoom level where text begins to fade out (was originally 2.0)
                        fade_window = 1.5  # Additional zoom required to become fully invisible
                        
                        if map_screen.camera.zoom > fade_start:
                            alpha_ratio = 1.0 - min(1.0, (map_screen.camera.zoom - fade_start) / fade_window)
                        else:
                            alpha_ratio = 1.0
                            
                        alpha = int(255 * alpha_ratio)

                        if alpha <= 0:
                            continue # Skip rendering entirely if fully transparent
                        # ---------------------------------------------
                        
                        scaled_w = int(surf.get_width() * map_screen.camera.zoom * land_scale)
                        scaled_h = int(surf.get_height() * map_screen.camera.zoom * land_scale)
                        
                        if scaled_w > 0 and scaled_h > 0:
                            scaled_text = pygame.transform.scale(surf, (scaled_w, scaled_h))
                            scaled_shadow = pygame.transform.scale(shadow, (scaled_w, scaled_h))
                            
                            angle = blob.get("angle", 0)
                            if abs(angle) > 2: 
                                scaled_text = pygame.transform.rotate(scaled_text, angle)
                                scaled_shadow = pygame.transform.rotate(scaled_shadow, angle)
                            
                            scaled_text.set_alpha(alpha)
                            scaled_shadow.set_alpha(alpha)
                            
                            # Center the rotated rect exactly on the calculated coordinates
                            txt_rect = scaled_text.get_rect(center=(int(sx), int(sy)))
                            
                            surface.blit(scaled_shadow, (txt_rect.x + 2, txt_rect.y + 2))
                            surface.blit(scaled_text, txt_rect)
                            
                            # Record that this country has successfully been drawn
                            drawn_countries.add(country)