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
    root.title("Select Countries to Skip")
    root.geometry("400x500")
    root.attributes("-topmost", True)
    root.focus_force()

    if not hasattr(map_ref, 'multiplayer_protected_countries'):
        map_ref.multiplayer_protected_countries = set()

    lbl = tk.Label(root, text="Select countries to skip (they will not take action this turn):", wraplength=380)
    lbl.pack(pady=(10, 5))

    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    canvas = tk.Canvas(frame)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    
    def configure_canvas(event):
        canvas.itemconfig(canvas_window, width=event.width)
    canvas.bind("<Configure>", configure_canvas)

    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    check_vars = {}
    
    countries = [cid for cid, data in map_ref.nation_data.items() if data.get("is_playable")]
    countries.sort(key=lambda c: map_ref.nation_data[c].get("name", c))
    
    for cid in countries:
        var = tk.BooleanVar(value=(cid in map_ref.multiplayer_protected_countries))
        check_vars[cid] = var
        name = map_ref.nation_data[cid].get("name", cid)
        cb = tk.Checkbutton(scrollable_frame, text=f"{name} ({cid})", variable=var)
        cb.pack(anchor="w", padx=5)
        
    def on_confirm():
        map_ref.multiplayer_protected_countries.clear()
        count = 0
        for cid, var in check_vars.items():
            if var.get():
                map_ref.multiplayer_protected_countries.add(cid)
                count += 1
        map_ref.show_feedback(f"{count} countries will give no moves this turn.")
        
        canvas.unbind_all("<MouseWheel>")
        root.quit()
        root.destroy()
        
    def on_closing():
        canvas.unbind_all("<MouseWheel>")
        root.quit()
        root.destroy()

    btn_frame = tk.Frame(root)
    btn_frame.pack(fill=tk.X, pady=10)
    
    confirm_btn = tk.Button(btn_frame, text="Confirm", command=on_confirm, width=15)
    confirm_btn.pack(side=tk.LEFT, padx=30)
    
    cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_closing, width=15)
    cancel_btn.pack(side=tk.RIGHT, padx=30)
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.eval('tk::PlaceWindow . center')
    
    root.mainloop()
