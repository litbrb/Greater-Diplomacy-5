import tkinter as tk
from tkinter import messagebox, colorchooser
import json
import os

PATH = "map_functions/data/countries_data.json"

class CountryEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Country Data Editor")
        self.data = self.load_data()

        # --- Editor UI (Top) ---
        editor_frame = tk.LabelFrame(root, text="Editor", padx=10, pady=10)
        editor_frame.pack(fill="x", padx=10, pady=5)

        self.color_preview = tk.Canvas(editor_frame, width=50, height=25, bg="grey", highlightthickness=1)
        self.color_preview.grid(row=0, column=2, padx=5)

        tk.Label(editor_frame, text="Country Name:").grid(row=0, column=0, sticky="w")
        self.name_ent = tk.Entry(editor_frame)
        self.name_ent.grid(row=0, column=1, sticky="we")

        self.color_btn = tk.Button(editor_frame, text="Pick Color", command=self.pick_color)
        self.color_btn.grid(row=1, column=0, columnspan=2, sticky="we", pady=5)
        self.current_color = [150, 150, 150]

        tk.Button(editor_frame, text="Save/Update Country", bg="#4CAF50", fg="white", 
                  command=self.save_country).grid(row=2, column=0, columnspan=3, sticky="we")

        # --- Country List UI (Bottom) ---
        tk.Label(root, text="Registered Countries:").pack(pady=(10, 0))
        
        list_container = tk.Frame(root)
        list_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(list_container)
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Mouse wheel binding for convenience
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.refresh_list()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def load_data(self):
        if os.path.exists(PATH):
            try:
                with open(PATH, "r") as f: return json.load(f)
            except: return {}
        return {}

    def pick_color(self):
        color = colorchooser.askcolor(title="Choose Country Color")
        if color[0]: 
            self.current_color = [int(c) for c in color[0]]
            hex_color = '#%02x%02x%02x' % tuple(self.current_color)
            self.color_preview.config(bg=hex_color)

    def save_country(self):
        name = self.name_ent.get().strip()
        if not name: 
            messagebox.showwarning("Error", "Name cannot be empty")
            return
        
        if name in self.data:
            self.data[name]["color"] = self.current_color
        else:
            self.data[name] = {
                "color": self.current_color,
                "research": {"cavalry": 0, "destroyer": 0, "armored_car": 0, "infantry": 1800},
                "money": 0,
                "manpower": 0,
                "materials": 0, 
                "fuel": 0,      
                "is_playable": True,
                "at_war_with": [],
                "allied_with": []
            }
        
        self.write_to_file()
        self.refresh_list()

    def delete_country(self, name):
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            del self.data[name]
            self.write_to_file()
            self.refresh_list()

    def write_to_file(self):
        with open(PATH, "w") as f:
            json.dump(self.data, f, indent=4)

    def load_into_editor(self, name):
        country = self.data[name]
        self.name_ent.delete(0, tk.END)
        self.name_ent.insert(0, name)
        self.current_color = country.get("color", [150, 150, 150])
        hex_color = '#%02x%02x%02x' % tuple(self.current_color)
        self.color_preview.config(bg=hex_color)

    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for name in sorted(self.data.keys()):
            country_row = tk.Frame(self.scrollable_frame, pady=2, padx=5)
            country_row.pack(fill="x", expand=True)

            rgb = self.data[name].get("color", [150, 150, 150])
            hex_color = '#%02x%02x%02x' % tuple(rgb)

            # Color Box
            tk.Label(country_row, bg=hex_color, width=4, relief="ridge").pack(side="left")
            # Name Label
            tk.Label(country_row, text=name, width=20, anchor="w", font=("Arial", 10)).pack(side="left", padx=5)
            
            # Action Buttons (Delete first so Edit is in a consistent spot)
            tk.Button(country_row, text="Del", fg="red", width=4, 
                      command=lambda n=name: self.delete_country(n)).pack(side="right", padx=2)
            tk.Button(country_row, text="Edit", width=6, 
                      command=lambda n=name: self.load_into_editor(n)).pack(side="right", padx=2)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("450x650")
    CountryEditor(root)
    root.mainloop()