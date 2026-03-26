import pygame
import json
import os
from gameState import GameState, SCREEN_WIDTH, SCREEN_HEIGHT
from ui_elements import Button

class Research_Screen(GameState):
    def __init__(self):
        super().__init__()
        self.bg_color = (20, 20, 30)
        self.map_screen = None
        self.research_template = {}
        
        # Load the master list of researchable techs
        template_path = "map_functions/data/research_template.json"
        if os.path.exists(template_path):
            with open(template_path, "r") as f:
                self.research_template = json.load(f)

    def start_research(self, map_ref):
        """Handoff from Controller."""
        self.map_screen = map_ref
        self.refresh_ui()

    def refresh_ui(self):
        # 1. Clear current buttons and add Back button
        self.elements = [
            Button(50, 50, "small", "red", "Back", self.exit_to_map)
        ]
        
        # 2. Safety Check: If no country is selected yet, don't try to load tech
        if not self.map_screen or self.map_screen.player_country == "None":
            return

        player = self.map_screen.player_country
        country_data = self.map_screen.nation_data.get(player, {})
        
        # 3. Ensure necessary dictionaries exist in the country's data
        res_levels = country_data.setdefault("research", {})
        queue = country_data.setdefault("research_queue", [])
        progress_cache = country_data.setdefault("research_progress", {}) 
        
        # 4. Use the TEMPLATE to loop so we see ALL techs, even if not in country JSON yet
        y_pos = 120
        x_start = 400 # Starting X for a vertical list
        column_count = 0
        
        # We sort them so the UI order is consistent
        sorted_techs = sorted(self.research_template.keys())

        for tech in sorted_techs:
            # Get current level (default to 0 if tech isn't in country dict yet)
            level = res_levels.get(tech, 0)
            
            # Is it currently being researched?
            queued_item = next((item for item in queue if item["tech_name"] == tech), None)
            
            if queued_item:
                # STATE: ACTIVE
                status_text = f"{tech.replace('_',' ').title()}: {queued_item['days_remaining']}d (PAUSE)"
                color = "green"
                callback = lambda t=tech: self.pause_research(t)
            
            elif len(queue) < 2:
                # STATE: AVAILABLE
                has_progress = tech in progress_cache
                # Formula: 30 base + (level * 15). If resumed, use saved value.
                days = progress_cache[tech] if has_progress else (30 + (level * 15))
                
                prefix = "Resume" if has_progress else "Start"
                status_text = f"{prefix} {tech.replace('_',' ').title()} (Lvl {level}): {days}d"
                color = "blue"
                callback = lambda t=tech: self.start_or_resume_research(t)
            
            else:
                # STATE: BLOCKED
                status_text = f"{tech.replace('_',' ').title()} (Slots Full)"
                color = "grey"
                callback = lambda: self.map_screen.show_feedback("Slots full! Pause something first.")

            # Create the button
            # Added logic to create a second column if the list is too long for the screen
            btn = Button(x_start + (column_count // 8 * 450), 120 + (column_count % 8 * 80), "large", color, status_text, callback)
            self.elements.append(btn)
            column_count += 1

    def start_or_resume_research(self, tech_name):
        player_data = self.map_screen.nation_data[self.map_screen.player_country]
        progress_cache = player_data.setdefault("research_progress", {})
        
        if tech_name in progress_cache:
            duration = progress_cache.pop(tech_name)
        else:
            current_level = player_data["research"].get(tech_name, 0)
            duration = 30 + (current_level * 15)

        new_project = {"tech_name": tech_name, "days_remaining": duration}
        player_data["research_queue"].append(new_project)
        self.refresh_ui()

    def pause_research(self, tech_name):
        player_data = self.map_screen.nation_data[self.map_screen.player_country]
        queue = player_data["research_queue"]
        progress_cache = player_data.setdefault("research_progress", {})

        for i, project in enumerate(queue):
            if project["tech_name"] == tech_name:
                progress_cache[tech_name] = project["days_remaining"]
                queue.pop(i)
                break
        
        self.map_screen.show_feedback(f"Paused {tech_name.replace('_',' ').title()}")
        self.refresh_ui()

    def exit_to_map(self):
        self.next_state = "MAP"
        self.done = True

    def additional_draw(self, surface):
        if not self.map_screen: return
        font = pygame.font.SysFont("Arial", 32)
        title_str = f"RESEARCH LAB: {self.map_screen.player_country.upper()}"
        title = font.render(title_str, True, (255, 255, 255))
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 40))

    def handle_back_key(self):
        self.exit_to_map()