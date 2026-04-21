# Used for logical ownership assignment
WATER_MAPPING = {
    "ocean": "Ocean", 
    "coastal_sea": "Ocean", 
    "inland_sea": "Ocean", 
    "lakes": "Lakes"
}

# Used in refresh_map.py so lakes render the same color as oceans on political maps
VISUAL_WATER_MAPPING = {
    "ocean": "Ocean", 
    "coastal_sea": "Ocean", 
    "inland_sea": "Ocean", 
    "lakes": "Ocean"
}

# Handy list to check if terrain is water in several movement/combat files
WATER_TERRAINS = ["ocean", "coastal_sea", "inland_sea", "lakes"]

# Owner groupings for logic and UI checks
WATER_NATIONS = ["Ocean", "Lakes"]
UNPLAYABLE_NATIONS = ["None", "Unclaimed", "Ocean", "Lakes"]

# Width and Height
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

UI_LEFT_OFFSET = 160

# Economy Data
BASE_YIELDS = {
    "manpower": 50,
    "materials": 50,
    "fuel": 0
}

UPKEEP_MODIFIER = 0.05

DAYS_PER_TURN = 10

# Non-core penalties
NON_CORE_MULTIPLIERS = {
    "manpower": 0.0,
    "materials": 0.5,
    "fuel": 0.5
}