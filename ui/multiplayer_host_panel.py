import pygame
import os
import secrets
import tkinter as tk
from tkinter import simpledialog, filedialog
from data.io import multiplayer_io
import data.constants as c



def load_multiplayer_moves(map_ref):
    root = tk.Tk()
    root.withdraw()
    
    files = filedialog.askopenfilenames(
        initialdir=c.MULTIPLAYER_SAVES_DIR,
        title="Select Move Files",
        filetypes=[("Move Files", "*.gd5move")]
    )
    if files:
        multiplayer_io.load_move_files(map_ref, files, getattr(map_ref, 'multiplayer_keys_dict', {}))
        map_ref.show_feedback(f"Loaded {len(files)} move files.")

def export_next_turn(map_ref):
    turn = map_ref.time_manager.total_turns
    export_path = os.path.join(c.MULTIPLAYER_SAVES_DIR, f"Turn_{turn}_Host.gd5tour")
    master_key = getattr(map_ref, 'multiplayer_master_key', '')
    keys_dict = getattr(map_ref, 'multiplayer_keys_dict', {})
    
    if not master_key or not keys_dict:
        map_ref.show_feedback("Error: Host keys missing. Did you init multiplayer?")
        return
        
    multiplayer_io.export_tournament(map_ref, export_path, master_key, keys_dict)
    
    # Reset protected countries for next turn
    map_ref.multiplayer_protected_countries = set()
    map_ref.show_feedback(f"Tournament exported to {export_path}")

def force_skip_player(map_ref):
    root = tk.Tk()
    root.withdraw()
    
    cid = simpledialog.askstring("Skip Player", "Enter Country ID to force skip (no AI):", parent=root)
    if cid and cid in map_ref.nation_data:
        if not hasattr(map_ref, 'multiplayer_protected_countries'):
            map_ref.multiplayer_protected_countries = set()
        map_ref.multiplayer_protected_countries.add(cid)
        map_ref.show_feedback(f"Country {cid} will give no moves this turn.")
    else:
        map_ref.show_feedback("Invalid Country ID.")
