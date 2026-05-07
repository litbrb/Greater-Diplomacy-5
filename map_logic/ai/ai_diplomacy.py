from map_logic.ai import ai_handler, ai_prompts
from data import queries
import data.constants as c

def process_basic_proactive_ai(map_screen):
    """Hardcoded basic logic for AI to declare war for cores and join faction wars."""
    active_nations = list(queries.get_living_nations(map_screen.map_data))
    ai_nations = queries.get_active_ai_nations(map_screen)
    
    # Grab the active players to pass down for our FULL/ABSOLUTE optimization check
    human_players = getattr(map_screen, 'active_players', [map_screen.player_country])

    # --- Trigger the UI Progress Bar ---
    map_screen.proactive_tasks_total = len(ai_nations)
    map_screen.proactive_tasks_completed = 0
    map_screen.loading_status_text = "Evaluating AI Grand Strategy..."

    for ai_name in ai_nations:
        if ai_name not in active_nations:
            map_screen.proactive_tasks_completed += 1
            continue

        data = map_screen.nation_data[ai_name]
        pending = data.setdefault("pending_diplomacy", {})
        my_faction = data.get("faction", "")
        my_enemies = data.get("at_war_with", [])
        
        # --- 0. Decrement Diplomatic Cooldowns ---
        if "diplo_cooldowns" in data:
            for target, actions in list(data["diplo_cooldowns"].items()):
                for act, cd in list(actions.items()):
                    if cd > 0:
                        actions[act] -= 1
                    elif cd == 0:
                        # Clean up finished cooldowns
                        del actions[act]
                if not actions:
                    del data["diplo_cooldowns"][target]

        is_already_at_war = len(my_enemies) > 0
        
        # --- 1. Unreachable Ceasefire Logic ---
        if is_already_at_war:
            for enemy in my_enemies:
                if enemy not in active_nations: continue
                if not queries.is_nation_reachable(ai_name, enemy, map_screen.map_data, map_screen.id_to_province, map_screen.nation_data):
                    if not queries.is_ai_diplo_on_cooldown(ai_name, enemy, "CEASEFIRE", map_screen.nation_data):
                        existing = pending.get(enemy, {})
                        turns = existing.get("turns", 0) if isinstance(existing, dict) else 0
                        
                        if enemy not in pending or turns == 0:
                            action_context = ai_prompts.get_proactive_action_context("CEASEFIRE")
                            llm_msg = ai_handler.generate_proactive_text(ai_name, enemy, action_context, human_players)
                            msg = llm_msg if llm_msg else ai_prompts.AI_FALLBACK_RESPONSES.get("GENERIC_MESSAGE", "We offer terms for a ceasefire.")
                            
                            pending[enemy] = {
                                "action": "CEASEFIRE",
                                "turns": 0,
                                "message": msg
                            }
                            queries.set_ai_diplo_cooldown(ai_name, enemy, "CEASEFIRE", map_screen.nation_data)
                            break # Act once per turn to avoid conflicts

        # --- 2. Call to Arms Logic ---
        if is_already_at_war and my_faction:
            faction_members = queries.get_faction_members(my_faction, map_screen.nation_data)
            for member in faction_members:
                if member == ai_name or member not in active_nations: continue
                
                member_enemies = map_screen.nation_data[member].get("at_war_with", [])
                unshared_wars = [e for e in my_enemies if e not in member_enemies and e in active_nations]
                
                if unshared_wars:
                    if not queries.is_ai_diplo_on_cooldown(ai_name, member, "CALL_TO_ARMS", map_screen.nation_data):
                        existing = pending.get(member, {})
                        turns = existing.get("turns", 0) if isinstance(existing, dict) else 0
                        
                        if member not in pending or turns == 0:
                            target_enemy = unshared_wars[0]
                            action_context = ai_prompts.get_proactive_action_context("CALL_TO_ARMS", target_enemy)
                            llm_msg = ai_handler.generate_proactive_text(ai_name, member, action_context, human_players)
                            msg = llm_msg if llm_msg else ai_prompts.AI_FALLBACK_RESPONSES.get("GENERIC_MESSAGE", "We request your aid in our ongoing conflicts!")
                            
                            pending[member] = {
                                "action": "CALL_TO_ARMS",
                                "turns": 0,
                                "message": msg
                            }
                            queries.set_ai_diplo_cooldown(ai_name, member, "CALL_TO_ARMS", map_screen.nation_data)
                            break # Act once per turn to avoid conflicts

        # --- 3. Faction War Joining Logic ---
        if my_faction:
            faction_members = queries.get_faction_members(my_faction, map_screen.nation_data)
            for member in faction_members:
                if member == ai_name:
                    continue
                
                member_enemies = map_screen.nation_data[member].get("at_war_with", [])
                unshared_wars = [e for e in member_enemies if e not in my_enemies and e in active_nations]
                
                if unshared_wars:
                    target_enemy = unshared_wars[0]
                    if not queries.is_ai_diplo_on_cooldown(ai_name, member, "JOIN_WARS", map_screen.nation_data):
                        existing = pending.get(member, {})
                        turns = existing.get("turns", 0) if isinstance(existing, dict) else 0
                        
                        if member not in pending or turns == 0:
                            action_context = ai_prompts.get_proactive_action_context("JOIN_WARS", target_enemy)
                            llm_msg = ai_handler.generate_proactive_text(ai_name, member, action_context, human_players)
                            msg = llm_msg if llm_msg else ai_prompts.AI_FALLBACK_RESPONSES.get("PROACTIVE_JOIN_WAR", "Brothers, let us join your fight.")
                            
                            pending[member] = {
                                "action": "JOIN_WARS",
                                "turns": 0,
                                "message": msg
                            }
                            queries.set_ai_diplo_cooldown(ai_name, member, "JOIN_WARS", map_screen.nation_data)
                            break # Act once per turn to avoid conflicts

        # --- 4. Declare War for Cores Logic (Border Check Only) ---
        if not is_already_at_war:
            current_turn = queries.get_total_turns(map_screen.time_manager)
            if current_turn >= c.AI_WAR_COOLDOWN_TURNS:
                targets_holding_cores = queries.get_nations_holding_our_cores(ai_name, map_screen.map_data)
                
                if targets_holding_cores:
                    # ONLY look at nations we actually share a physical border with
                    my_neighbors = queries.get_neighboring_nations(ai_name, map_screen.map_data, map_screen.id_to_province)
                    valid_border_targets = [t for t in targets_holding_cores if t in my_neighbors]
                    
                    for target in valid_border_targets:
                        if target not in active_nations: continue
                        if target in my_enemies: continue
                        if queries.are_in_same_faction(ai_name, target, map_screen.nation_data): continue
                        
                        # Check localized border strength instead of global strength
                        my_border_str, target_border_str = queries.get_border_strength(ai_name, target, map_screen.map_data, map_screen.id_to_province)
                        
                        # Prevent division by zero if they have literally no troops on the border
                        target_border_str = max(1, target_border_str)
                        
                        # --- NEW: Consider total alliance strength and economy ---
                        my_alliance_str = queries.get_alliance_military_strength(ai_name, map_screen.map_data, map_screen.nation_data)
                        target_alliance_str = queries.get_alliance_military_strength(target, map_screen.map_data, map_screen.nation_data)
                        
                        my_econ_power = queries.get_economic_power(ai_name, map_screen.nation_data) / 100.0
                        target_econ_power = queries.get_economic_power(target, map_screen.nation_data) / 100.0
                        
                        my_total_power = my_alliance_str + my_econ_power
                        target_total_power = max(1.0, target_alliance_str + target_econ_power)
                        # ---------------------------------------------------------
                        
                        # AI needs local border superiority AND overall global viability to declare war
                        if my_border_str >= (target_border_str * c.AI_WAR_STRENGTH_THRESHOLD) and my_total_power >= (target_total_power * c.AI_GLOBAL_STRENGTH_THRESHOLD):
                            if not queries.is_ai_diplo_on_cooldown(ai_name, target, "WAR_DECLARATION", map_screen.nation_data):
                                existing = pending.get(target, {})
                                turns = existing.get("turns", 0) if isinstance(existing, dict) else 0
                                
                                if target not in pending or turns == 0:
                                    action_context = ai_prompts.get_proactive_action_context("WAR_DECLARATION", target)
                                    llm_msg = ai_handler.generate_proactive_text(ai_name, target, action_context, human_players)
                                    msg = llm_msg if llm_msg else ai_prompts.AI_FALLBACK_RESPONSES.get("PROACTIVE_DECLARE_WAR", "Your occupation of our rightful territory ends now!")

                                    pending[target] = {
                                        "action": "WAR_DECLARATION",
                                        "turns": 0,
                                        "message": msg
                                    }
                                    queries.set_ai_diplo_cooldown(ai_name, target, "WAR_DECLARATION", map_screen.nation_data)
                                    break
                        
        # --- Update Progress Bar ---
        map_screen.proactive_tasks_completed += 1
        map_screen.loading_status_text = f"Evaluating AI Grand Strategy ({map_screen.proactive_tasks_completed}/{map_screen.proactive_tasks_total})..."