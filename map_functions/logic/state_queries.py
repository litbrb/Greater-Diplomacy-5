from data.constants import WATER_TERRAINS

def is_province_in_active_combat(province, nation_data):
    """Returns True if ANY units from mutually hostile nations occupy this province."""
    units = province.get("units", [])
    if len(units) < 2:
        return False
        
    owners_present = list(set(u.get("owner") for u in units if u.get("owner")))
    
    for i in range(len(owners_present)):
        for j in range(i + 1, len(owners_present)):
            nation_a = nation_data.get(owners_present[i], {})
            if owners_present[j] in nation_a.get("at_war_with", []):
                return True
    return False

def is_nation_in_combat_here(nation, province, nation_data):
    """Returns True if the specified nation has units in the province that are actively engaged with enemy units."""
    units = province.get("units", [])
    enemies = nation_data.get(nation, {}).get("at_war_with", [])
    return any(u.get("owner") in enemies for u in units)

def is_hostile_territory(moving_nation, target_owner, nation_data):
    """Checks if a nation is actively at war with the target territory."""
    if target_owner in ["None", "Unclaimed", "Ocean", "Lakes"]:
        return False
    
    enemies = nation_data.get(moving_nation, {}).get("at_war_with", [])
    return target_owner in enemies

def can_ships_enter(moving_nation, target_province, nation_data):
    """Centralized rules for naval movement."""
    is_water = target_province.get("terrain") in WATER_TERRAINS
    if is_water:
        return True
        
    if not target_province.get("is_coastal", False):
        return False
        
    target_owner = target_province.get("owner", "Unclaimed")
    allies = nation_data.get(moving_nation, {}).get("allied_with", [])
    
    # Ships can only enter friendly or unowned ports
    return target_owner == moving_nation or target_owner in allies or target_owner == "Unclaimed"

def can_land_units_enter(moving_nation, target_province, nation_data):
    """Centralized rules for land movement."""
    if target_province.get("terrain") in WATER_TERRAINS:
        return False

    target_owner = target_province.get("owner", "Unclaimed")
    allies = nation_data.get(moving_nation, {}).get("allied_with", [])
    enemies = nation_data.get(moving_nation, {}).get("at_war_with", [])

    # Whitelist neutral water countries so they act as open international waters
    allowed_owners = ["Unclaimed", "None", moving_nation, "Ocean", "Lakes"]

    if target_owner not in allowed_owners:
        if not (target_owner in enemies or target_owner in allies):
            return False

    return True