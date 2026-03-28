import pygame
import json
import os
from gameState import GameState, SCREEN_WIDTH, SCREEN_HEIGHT
from ui_elements import Button
from screens.map_related_screens import recruit_ui

class Recruit_Screen(GameState):
    def __init__(self, is_naval=False):
        super().__init__()
        self.target_province = None
        self.map_screen = None
        self.cancel_hitboxes = []
        self.is_naval = is_naval
        self.unit_library = self.load_unit_data()

    def load_unit_data(self):
        path = 'map_functions/data/unit_data.json'
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {}

    def start_with_province(self, province, map_ref):
        self.target_province = province
        self.map_screen = map_ref
        self.refresh_ui()

    def refresh_ui(self):
        self.elements = [Button(50, 50, "small", "red", "Back", self.exit_to_map)]
        
        y_offset = 150
        # Filter units: Naval screen shows naval units, Recruit screen shows land units
        for name, stats in self.unit_library.items():
            if stats.get("naval_unit", False) == self.is_naval:
                # Create a descriptive label
                cost_str = f"{stats.get('cost_money', 0)}M"
                if stats.get("cost_materials"): cost_str += f", {stats['cost_materials']}Mat"
                if stats.get("cost_manpower"): cost_str += f", {stats['cost_manpower']}Man"
                if stats.get("cost_fuel"): cost_str += f", {stats['cost_fuel']}Fue"
                
                txt = f"{name} ({cost_str})"
                # land units use green, naval use blue
                color = "blue" if self.is_naval else "green"
                
                btn = Button(100, y_offset, "large", color, txt, lambda n=name: self.buy_unit(n))
                self.elements.append(btn)
                y_offset += 90
                
                if y_offset > SCREEN_HEIGHT - 100: break # Simple overflow protection

    def buy_unit(self, unit_name):
        stats = self.unit_library.get(unit_name)
        if not stats or not self.map_screen: return

        # Resource Check
        p_data = self.map_screen.nation_data[self.map_screen.player_country]
        
        can_afford = (
            p_data.get("money", 0) >= stats.get("cost_money", 0) and
            p_data.get("manpower", 0) >= stats.get("cost_manpower", 0) and
            p_data.get("materials", 0) >= stats.get("cost_materials", 0) and
            p_data.get("fuel", 0) >= stats.get("cost_fuel", 0)
        )

        if can_afford:
            # Deduct all resources
            p_data["money"] -= stats.get("cost_money", 0)
            p_data["manpower"] -= stats.get("cost_manpower", 0)
            p_data["materials"] -= stats.get("cost_materials", 0)
            p_data["fuel"] -= stats.get("cost_fuel", 0)

            # Add to deployment queue
            order = {
                "unit_type": unit_name,
                "days_remaining": stats.get("production_time", 5),
                "cost": stats.get("cost_money", 0) # For potential refunds
            }
            self.target_province.setdefault("deployment_queue", []).append(order)
            self.map_screen.show_feedback(f"Ordered {unit_name}!")
            self.refresh_ui()
        else:
            self.map_screen.show_feedback("Insufficient resources!")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for rect, index in self.cancel_hitboxes:
                    if rect.collidepoint(mouse_pos):
                        self.cancel_order(index)
                        return
            for el in self.elements:
                el.handle_event(event)

    def cancel_order(self, index):
        queue = self.target_province.get("deployment_queue", [])
        if 0 <= index < len(queue):
            queue.pop(index)
            self.refresh_ui()

    def additional_draw(self, surface):
        if self.target_province:
            self.cancel_hitboxes = recruit_ui.draw_recruitment_overlay(surface, self.target_province)
            title_text = "Naval Construction" if self.is_naval else "Army Recruitment"
            font = pygame.font.SysFont("Arial", 32)
            ts = font.render(f"{title_text}: Prov {self.target_province['id']}", True, (255, 255, 255))
            surface.blit(ts, (SCREEN_WIDTH//2 - ts.get_width()//2, 50))

    def exit_to_map(self):
        self.next_state, self.done = "MAP", True

    def handle_back_key(self):
        self.exit_to_map()