import json
import os
from map_functions.logic import diplomacy_logic

def process_next_turn(self):
    days_to_advance = 5
    self.time_manager.process_time(days_to_advance)
    
    # 1. Process Diplomacy
    diplomacy_logic.process_diplomacy_turn(self)

    process_movement(self)
    
    # 2. Process Economy
    process_economy(self)
    
    # 3. Process Recruitment
    process_recruitment(self, days_to_advance)

def process_movement(self):
    moving_units = []
    for province in self.map_data.values():
        units_to_keep = []
        for unit in province.get("units", []):
            order = unit.get("order")
            # We now check for a 'path' list
            if order and order.get("type") == "MOVE" and order.get("path"):
                unit["_current_province_id"] = province["id"]
                moving_units.append(unit)
            else:
                units_to_keep.append(unit)
        province["units"] = units_to_keep

    if not moving_units:
        return

    # Ensure every moving unit has a valid speed stat, in case a unit somehow loses it's speed stat
    max_speed = 0
    if moving_units:
        max_speed = max(unit.get("speed", 1) for unit in moving_units)

    for step in range(max_speed):
        for unit in moving_units:
            order = unit.get("order")
            # If the path is empty, they are done for the turn
            if not order or not order.get("path"):
                continue

            # Units move 1 tile per step. Take the first tile from the path.
            target_id = order["path"][0]
            target_prov = self.id_to_province.get(target_id)

            if not target_prov:
                order["path"] = [] # Error fallback
                continue

            # Collision/Ownership logic
            old_owner = target_prov.get("owner", "empty")
            player_data = self.nation_data.get(unit["owner"], {})
            at_war = old_owner in player_data.get("at_war_with", [])
            is_allied = old_owner in player_data.get("allied_with", [])
            is_self = old_owner == unit["owner"]
            is_empty = old_owner == "empty"
            enemy_present = any(u["owner"] in player_data.get("at_war_with", []) for u in target_prov.get("units", []))

            can_enter = is_empty or is_self or at_war or is_allied
            
            if can_enter and not enemy_present:
                unit["_current_province_id"] = target_id
                # Remove the tile we just moved to from the remaining path
                order["path"].pop(0)
                
                if is_empty or at_war:
                    from map_functions.logic import edit_province_ownership
                    edit_province_ownership.conquer_province(self, target_prov, unit["owner"])
            else:
                # BLOCKED: Stop and cancel the rest of the path
                order["path"] = []

    # Finalize positions
    for unit in moving_units:
        final_prov = self.id_to_province.get(unit["_current_province_id"])
        if "_current_province_id" in unit:
            del unit["_current_province_id"]
        final_prov["units"].append(unit)

def process_economy(self):
    """Calculates income for ALL countries based on the provinces they own."""
    BASE_TAX = 10
    
    # 1. Tracker for this turn's earnings
    turn_income = {name: 0 for name in self.nation_data.keys()}

    # 2. Sum up province income
    for province in self.map_data.values():
        owner = province.get("owner")
        if owner in turn_income and owner != "None":
            turn_income[owner] += BASE_TAX

    # 3. Update the actual data
    player_earned = 0
    for country_name, amount in turn_income.items():
        if country_name in self.nation_data:
            self.nation_data[country_name]["money"] += amount
            # Manpower could have its own logic, but adding for now
            self.nation_data[country_name]["manpower"] = self.nation_data[country_name].get("manpower", 0) + amount
            
            if country_name == self.player_country:
                player_earned = amount

    return player_earned

def process_recruitment(self, days_passed):
    """Handles the deployment of units from the queue to the field."""
    
    # --- Load Unit Data for Stats Lookup ---
    unit_stats_path = 'map_functions/data/unit_data.json'
    unit_library = {}
    
    if os.path.exists(unit_stats_path):
        with open(unit_stats_path, 'r') as f:
            unit_library = json.load(f)

    for province in self.map_data.values():
        queue = province.get("deployment_queue", [])
        if not queue:
            continue
            
        # We use a list comprehension to find what's finished 
        # and keep what's still cooking
        still_deploying = []
        
        for item in queue:
            # Each 'Next Turn' represents 5 days
            item["days_remaining"] -= days_passed
            
            if item["days_remaining"] <= 0:
                # 1. Identify owner at time of deployment
                current_owner = province.get("owner", "None")
                unit_type = item["unit_type"]
                
                # 2. Look up starting health from unit_data.json
                # Default to 100 if the unit type isn't found in the JSON
                stats = unit_library.get(unit_type, {})
                max_health = stats.get("health", 100)
                unit_speed = stats.get("speed", 1) # <--- GET SPEED HERE
                
                # 3. Create the unified Unit JSON object
                new_unit_data = {
                    "type": unit_type,
                    "owner": current_owner,
                    "health": max_health,
                    "max_health": max_health, # Useful for showing health bars later
                    "speed": unit_speed, # <--- ADD SPEED HERE
                    "order": {"type": "MOVE", "path": []} # Initialize with an empty path list
                }
                
                province["units"].append(new_unit_data)
            else:
                # Keep in queue
                still_deploying.append(item)
        
        # Update the province queue with only the remaining items
        province["deployment_queue"] = still_deploying