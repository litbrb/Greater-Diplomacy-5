import data.constants as c
from data import queries
from ui import buttons

def select_player_country(map_screen, province):
    owner = province.get("owner", "Unclaimed")
    if owner in map_screen.nation_data and map_screen.nation_data[owner].get("is_playable"):
        map_screen.pending_selection = owner
        map_screen.selected_province = province 
        map_screen.show_feedback(f"Selected {owner.title()}...")
    else:
        map_screen.show_feedback("Cannot select unowned or non-playable territory")

def confirm_player_country(map_screen):
    if map_screen.pending_selection:
        map_screen.active_players.append(map_screen.pending_selection)
        
        map_screen.selected_province = None 
        map_screen.hovered_province = None
        map_screen.hover_glow_surf = None
        
        if len(map_screen.active_players) < map_screen.num_players:
            map_screen.show_feedback(f"Player {len(map_screen.active_players) + 1}, pick a country!")
            map_screen.pending_selection = None
        else:
            # Everyone picked, start with Player 1
            map_screen.current_player_index = 0
            map_screen.player_country = map_screen.active_players[0]
            map_screen.selection_mode = False
            map_screen.pending_selection = None
            
            map_screen.show_feedback(f"Now playing as {map_screen.player_country}")
            buttons.render_buttons(map_screen)
            map_screen.refresh_relations_map()

def start_spectator(map_screen):
    map_screen.player_country = "Spectator"
    if "Spectator" not in map_screen.nation_data:
        map_screen.nation_data["Spectator"] = {
            "name": "Spectator",
            "color": [200, 200, 200],
            "is_playable": False,
            "at_war_with": [],
            "allied_with": [],
            "pending_diplomacy": {}
        }
    map_screen.active_players.append("Spectator")
    
    if len(map_screen.active_players) < map_screen.num_players:
        map_screen.show_feedback(f"Player {len(map_screen.active_players) + 1}, pick a country!")
        map_screen.pending_selection = None
    else:
        map_screen.current_player_index = 0
        map_screen.player_country = map_screen.active_players[0]
        map_screen.selection_mode = False
        map_screen.pending_selection = None
        map_screen.show_feedback(f"Now playing as {map_screen.player_country}")
        
        buttons.render_buttons(map_screen)
        map_screen.refresh_relations_map()
        
def cancel_selection(map_screen):
    map_screen.pending_selection = None
    map_screen.selected_province = None