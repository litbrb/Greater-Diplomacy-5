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
    # 1. Clear units from map and store those with orders
    for province in self.map_data.values():
        units_to_keep = []
        for unit in province.get("units", []):
            order = unit.get("order")
            if order and order.get("type") == "MOVE" and order.get("path"):
                unit["_current_province_id"] = province["id"]
                moving_units.append(unit)
            else:
                units_to_keep.append(unit)
        province["units"] = units_to_keep

    if not moving_units: return

    max_speed = max(unit.get("speed", 1) for unit in moving_units)

    # 2. Process steps
    for step in range(max_speed):
        for unit in moving_units:
            order = unit.get("order")
            if not order or not order.get("path"): continue

            target_id = order["path"][0]
            target_prov = self.id_to_province.get(target_id)
            if not target_prov: continue

            player_data = self.nation_data.get(unit["owner"], {})
            dest_owner = target_prov.get("owner", "empty")
            
            at_war = dest_owner in player_data.get("at_war_with", [])
            is_allied = dest_owner in player_data.get("allied_with", [])
            is_self = dest_owner == unit["owner"]
            is_empty = dest_owner == "empty"

            # COMBAT CHECK: Is an enemy unit physically present right now?
            # We check both stationary units and units that already moved this step
            enemy_unit_present = any(u["owner"] in player_data.get("at_war_with", []) 
                                   for u in target_prov.get("units", []))

            # Logic: Can enter if empty, allied, self, or at war.
            can_enter_territory = is_empty or is_self or at_war or is_allied
            
            if can_enter_territory:
                # Move unit logically
                unit["_current_province_id"] = target_id
                order["path"].pop(0)

                # Capture logic
                if is_empty or at_war:
                    from map_functions.logic import edit_province_ownership
                    edit_province_ownership.conquer_province(self, target_prov, unit["owner"])

                # STOP LOGIC: If we moved onto a tile with an enemy unit, 
                # we MUST stop here to fight, regardless of remaining speed/path.
                if enemy_unit_present:
                    order["path"] = [] 
            else:
                # BLOCKED by neutral/non-allied borders
                order["path"] = []

        # 3. CRITICAL: Place units back into provinces briefly after each sub-step
        # This ensures that units moving later in the same "step" see units that moved earlier
        for unit in moving_units:
            prov = self.id_to_province.get(unit["_current_province_id"])
            if unit not in prov["units"]:
                prov["units"].append(unit)
        
        # Now clear them again for the next sub-step (except those who finished)
        if step < max_speed - 1:
            for province in self.map_data.values():
                province["units"] = [u for u in province["units"] if u not in moving_units]

    # Final cleanup of temp variables
    for unit in moving_units:
        if "_current_province_id" in unit: del unit["_current_province_id"]

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