import random

def get_pending_action(nation_data, player_name, target_name):
    """Helper to safely read the pending action, handling both new dicts and old strings."""
    pending = nation_data.get(player_name, {}).get("pending_diplomacy", {})
    info = pending.get(target_name)
    if isinstance(info, dict):
        return info.get("action")
    return info # Fallback if it's an old string from a previous save

def toggle_diplomacy_action(nation_data, player_name, target_name, action_type):
    pending = nation_data[player_name].setdefault("pending_diplomacy", {})
    current_action = get_pending_action(nation_data, player_name, target_name)
    
    if current_action == action_type:
        info = pending.get(target_name, {})
        if isinstance(info, dict) and info.get("turns", 0) > 0:
            return "Cannot undo! The diplomat has already crossed their borders."
            
        del pending[target_name]
        return f"Undo {action_type.replace('_', ' ').title()}"
        
    elif current_action is not None:
        # Prevents declaring war while an alliance request is pending, etc.
        return "A diplomatic action is already pending with this nation!"
    else:
        pending[target_name] = {"action": action_type, "turns": 0}
        return "Message drafted. Will send at end of turn."

def queue_text_message(nation_data, player_name, target_name, content):
    pending = nation_data[player_name].setdefault("pending_diplomacy", {})
    current_action = get_pending_action(nation_data, player_name, target_name)
    
    # Allow overwriting if the pending action is a drafted message, otherwise block it
    if current_action is not None and not current_action.startswith("MSG:"):
        return "A diplomatic action is already pending with this nation!"
        
    pending[target_name] = {"action": f"MSG:{content}", "turns": 0}
    return "Message draft saved. Will send at end of turn."

def cancel_text_message(nation_data, player_name, target_name):
    """Safely clears a drafted text message if it hasn't been sent yet."""
    pending = nation_data[player_name].setdefault("pending_diplomacy", {})
    current_action = get_pending_action(nation_data, player_name, target_name)
    
    if current_action and current_action.startswith("MSG:"):
        info = pending.get(target_name, {})
        if isinstance(info, dict) and info.get("turns", 0) > 0:
            return "Cannot undo! Message is already in transit."
            
        del pending[target_name]
        return "Draft cleared."
    return "No drafted message to clear."

def send_message(nation_data, sender, receiver, content, msg_type="TEXT"):
    receiver_data = nation_data.get(receiver)
    if not receiver_data: return
    if "inbox" not in receiver_data:
        receiver_data["inbox"] = []
    
    # Insert at the beginning so newest messages are at the top
    receiver_data["inbox"].insert(0, {
        "sender": sender,
        "content": content,
        "type": msg_type,
        "read": False
    })

def process_diplomacy_turn(self):
    """Called during turn_processor.py to finalize declarations and messages."""
    
    # --- 1. SIMULTANEOUS ACTION CLASH RESOLUTION ---
    # Detect if two nations fired an action at each other on the exact same turn
    nations = list(self.nation_data.keys())
    for i in range(len(nations)):
        for j in range(i + 1, len(nations)):
            nation_a = nations[i]
            nation_b = nations[j]
            
            a_data = self.nation_data[nation_a].get("pending_diplomacy", {})
            b_data = self.nation_data[nation_b].get("pending_diplomacy", {})
            
            a_info = a_data.get(nation_b)
            b_info = b_data.get(nation_a)
            
            # If both queued an action on the same turn (turns == 0)
            if isinstance(a_info, dict) and a_info.get("turns", 0) == 0 and \
               isinstance(b_info, dict) and b_info.get("turns", 0) == 0:
               
                a_action = a_info.get("action")
                b_action = b_info.get("action")
               
                # CLASH A: Mutual Alliance
                if a_action == "ALLIANCE_REQUEST" and b_action == "ALLIANCE_REQUEST":
                    finalize_alliance(self.nation_data, nation_a, nation_b)
                    send_message(self.nation_data, nation_a, nation_b, "Our mutual alliance proposals crossed paths. We are now allied!", "DIPLOMACY")
                    send_message(self.nation_data, nation_b, nation_a, "Our mutual alliance proposals crossed paths. We are now allied!", "DIPLOMACY")
                    del a_data[nation_b]
                    del b_data[nation_a]
                   
                # CLASH B: War vs Peace (War overwrites peace)
                elif a_action == "WAR_DECLARATION" and b_action in ["ALLIANCE_REQUEST", "CEASEFIRE"]:
                    send_message(self.nation_data, nation_a, nation_b, f"Your diplomat proposing a {b_action.split('_')[0].lower()} was executed. We are at WAR!", "DIPLOMACY")
                    del b_data[nation_a] # B's peaceful request is destroyed
                    
                elif b_action == "WAR_DECLARATION" and a_action in ["ALLIANCE_REQUEST", "CEASEFIRE"]:
                    send_message(self.nation_data, nation_b, nation_a, f"Your diplomat proposing a {a_action.split('_')[0].lower()} was executed. We are at WAR!", "DIPLOMACY")
                    del a_data[nation_b] # A's peaceful request is destroyed
                   
                # CLASH C: Mutual Ceasefire
                elif a_action == "CEASEFIRE" and b_action == "CEASEFIRE":
                    finalize_neutral(self.nation_data, nation_a, nation_b)
                    send_message(self.nation_data, nation_a, nation_b, "Mutual ceasefire agreements signed.", "DIPLOMACY")
                    send_message(self.nation_data, nation_b, nation_a, "Mutual ceasefire agreements signed.", "DIPLOMACY")
                    del a_data[nation_b]
                    del b_data[nation_a]

    # --- 2. STANDARD RESOLUTION ---
    for country_name, data in self.nation_data.items():
        pending = data.get("pending_diplomacy", {})
        actions_to_clear = []

        for target, info in pending.items():
            # Handle old string format if loading a legacy save
            if isinstance(info, str):
                info = {"action": info, "turns": 1}
                pending[target] = info

            action = info.get("action", "")
            turns = info.get("turns", 0)

            if turns == 0:
                # Phase 1 (End of Turn 0): Apply unilateral effects & log messages to your outbox
                if action == "WAR_DECLARATION":
                    finalize_war(self.nation_data, country_name, target)
                    send_message(self.nation_data, country_name, target, "We have declared WAR upon you!", "DIPLOMACY")
                    send_message(self.nation_data, f"To: {target}", country_name, "We have declared WAR upon you!", "DIPLOMACY")
                elif action == "BREAK_ALLIANCE":
                    finalize_neutral(self.nation_data, country_name, target)
                    send_message(self.nation_data, country_name, target, "We have broken our alliance.", "DIPLOMACY")
                    send_message(self.nation_data, f"To: {target}", country_name, "We have broken our alliance.", "DIPLOMACY")
                elif action.startswith("MSG:"):
                    content = action[4:]
                    send_message(self.nation_data, country_name, target, content, "TEXT")
                    send_message(self.nation_data, f"To: {target}", country_name, content, "TEXT")
                elif action == "ALLIANCE_REQUEST":
                    send_message(self.nation_data, country_name, target, "We propose an alliance between our nations.", "DIPLOMACY")
                    send_message(self.nation_data, f"To: {target}", country_name, "We propose an alliance between our nations.", "DIPLOMACY")
                elif action == "CEASEFIRE":
                    send_message(self.nation_data, country_name, target, "We offer terms for a ceasefire.", "DIPLOMACY")
                    send_message(self.nation_data, f"To: {target}", country_name, "We offer terms for a ceasefire.", "DIPLOMACY")

                # Advance all actions to Phase 2
                info["turns"] = 1
                
            elif turns == 1:
                # Phase 2 (End of Round 1 for AI, End of Round 2 for Humans): Bilateral effects apply
                is_human_target = target in getattr(self, 'active_players', [])

                if action == "WAR_DECLARATION":
                    if not is_human_target:
                        send_message(self.nation_data, target, country_name, "You will regret this betrayal.", "TEXT")
                elif action == "BREAK_ALLIANCE":
                    if not is_human_target:
                        send_message(self.nation_data, target, country_name, "We won't forget this.", "TEXT")
                elif action.startswith("MSG:"):
                    if not is_human_target:
                        send_message(self.nation_data, target, country_name, "Message received.", "TEXT")
                    
                elif action == "ALLIANCE_REQUEST":
                    if is_human_target:
                        # If it survived to this phase, the human player ignored it during their turn!
                        send_message(self.nation_data, target, country_name, "Your alliance proposal was ignored and has expired.", "DIPLOMACY")
                    else:
                        # 50% chance for the AI to accept or decline your request
                        if random.random() > 0.5:
                            finalize_alliance(self.nation_data, country_name, target)
                            send_message(self.nation_data, target, country_name, "We happily accept your alliance proposal.", "DIPLOMACY")
                        else:
                            send_message(self.nation_data, target, country_name, "We decline your alliance proposal.", "DIPLOMACY")
                        
                elif action == "CEASEFIRE":
                    if is_human_target:
                        # If it survived to this phase, the human player ignored it during their turn!
                        send_message(self.nation_data, target, country_name, "Your ceasefire offer was ignored and has expired.", "DIPLOMACY")
                    else:
                        if random.random() > 0.5:
                            finalize_neutral(self.nation_data, country_name, target)
                            send_message(self.nation_data, target, country_name, "We accept your terms for a ceasefire.", "DIPLOMACY")
                        else:
                            send_message(self.nation_data, target, country_name, "We reject your ceasefire. The war continues.", "DIPLOMACY")
                
                # Action is fully resolved (or expired), queue it for cleanup
                actions_to_clear.append(target)

        # Cleanup resolved actions
        for t in actions_to_clear:
            del pending[t]

def finalize_war(nation_data, a, b):
    for country, other in [(a, b), (b, a)]:
        if other not in nation_data[country]["at_war_with"]:
            nation_data[country]["at_war_with"].append(other)
        if other in nation_data[country]["allied_with"]:
            nation_data[country]["allied_with"].remove(other)

def finalize_alliance(nation_data, a, b):
    for country, other in [(a, b), (b, a)]:
        if other not in nation_data[country]["allied_with"]:
            nation_data[country]["allied_with"].append(other)
        if other in nation_data[country]["at_war_with"]:
            nation_data[country]["at_war_with"].remove(other)

def finalize_neutral(nation_data, a, b):
    """Resets both countries to neutral."""
    for country, other in [(a, b), (b, a)]:
        if other in nation_data[country]["at_war_with"]:
            nation_data[country]["at_war_with"].remove(other)
        if other in nation_data[country]["allied_with"]:
            nation_data[country]["allied_with"].remove(other)