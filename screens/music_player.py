import pygame
import os
from data import queries
import ui_elements 
from gameState import GameState
from ui_elements import Button, Slider, process_text_input
from map_logic.rendering.font_manager import fonts
import data.constants as c

song_y = 32

class Music_Player(GameState):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.bg_color = (25, 25, 30)
        self.return_state = "MENU"
        
        # Ensure directories and files exist
        if not os.path.exists(c.MUSIC_DIR):
            os.makedirs(c.MUSIC_DIR)
        
        self.album_scroll_y = 0
        self.track_scroll_y = 0
        
        self.refresh_ui()

    def refresh_ui(self):
        self.elements = [
            Button(20, 20, "small", "red", "Back", self.handle_back_key)
        ]
        
        # --- Audio Sliders ---
        slider_x = c.SCREEN_WIDTH - 250
        
        self.elements.append(Slider(slider_x, 40, 200, "SFX Vol", self.controller.sfx_volume, self.set_sfx_volume))
        if c.USE_SOLOUD:
            self.elements.append(Slider(slider_x, 100, 200, "SFX Pitch", self.controller.sfx_pitch, self.set_sfx_pitch))

        self.elements.append(Slider(slider_x, 180, 200, "Music Vol", self.controller.music_volume, self.set_music_volume))
        if c.USE_SOLOUD:
            self.elements.append(Slider(slider_x, 240, 200, "Music Pitch", self.controller.music_pitch, self.set_music_pitch))
        
        y_offset = 120 + self.album_scroll_y
        
        # --- Left Column: Albums ---
        for album in sorted(self.controller.all_albums.keys()):
            is_active = album in self.controller.active_albums
            color = "green" if is_active else "grey"
            
            # --- IMPROVED COVER ART SEARCH ---
            album_dir = os.path.join(c.MUSIC_DIR, album)
            icon_img = None
            
            if os.path.exists(album_dir):
                # Search the album folder for ANY valid image file to use as the cover art
                for file in os.listdir(album_dir):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        try:
                            icon_path = os.path.join(album_dir, file)
                            raw_img = pygame.image.load(icon_path).convert_alpha()
                            icon_img = pygame.transform.smoothscale(raw_img, (180, 160))
                            break # Found an image, stop searching
                        except Exception as e:
                            print(f"Error loading icon {file} for {album}: {e}")
            
            if icon_img:
                # Spawn as a large vertical square if an icon is found
                self.elements.append(Button(20, y_offset, "album_square", color, album, 
                                            lambda a=album: self.toggle_album(a), 
                                            image=icon_img, show_text=True, layout="vertical"))
                y_offset += 210 # 200 height + 10 padding
            else:
                # Fallback to standard horizontal layout button if no image is present
                self.elements.append(Button(20, y_offset, "medium", color, album, lambda a=album: self.toggle_album(a)))
                y_offset += 60

        # --- Right Column: Tracks ---
        track_y = 80 + self.track_scroll_y
        
        self.elements.append(Button(c.MUSIC_LEFT_PANE_W + 20, track_y, "medium", "green", "Skip / Random Song", self.play_track))
        track_y += 60
        
        for track_path in self.controller.playlist:
            track_name = os.path.basename(track_path)
            is_playing = (self.controller.now_playing == track_path)
            color = "orange" if is_playing else "grey"
            
            self.elements.append(Button(c.MUSIC_LEFT_PANE_W + 20, track_y, "song", color, track_name, lambda p=track_path: self.play_track(p)))
            track_y += song_y

    def play_track(self, track_path=None):
        """Helper to play a track and instantly update the UI colors."""
        if track_path:
            self.controller.play_specific_song(track_path)
        else:
            self.controller.play_random_song()
        self.refresh_ui()

    # --- AUDIO MODIFICATION HANDLERS ---
    def set_sfx_volume(self, val):
        self.controller.sfx_volume = val
        ui_elements.global_sfx_volume = val    
        
        # If using pygame mixer, update the loaded sounds live
        if not c.USE_SOLOUD:
            if getattr(ui_elements, 'pygame_click_sound', None):
                ui_elements.pygame_click_sound.set_volume(val)
            if getattr(ui_elements, 'pygame_slider_sound', None):
                ui_elements.pygame_slider_sound.set_volume(val)
                
        self.save_audio_settings()

    def set_music_volume(self, val):
        self.controller.music_volume = val
        if c.USE_SOLOUD:
            if self.controller.music_handle is not None:
                self.controller.soloud.set_volume(self.controller.music_handle, val)
        else:
            pygame.mixer.music.set_volume(val)
        self.save_audio_settings()

    def set_music_pitch(self, val):
        self.controller.music_pitch = val
        if self.controller.music_handle is not None:
            speed_mult = 0.5 + (val * 1.5) 
            self.controller.soloud.set_relative_play_speed(self.controller.music_handle, speed_mult)
        self.save_audio_settings()
        
    def set_sfx_pitch(self, val):
        self.controller.sfx_pitch = val
        ui_elements.global_sfx_pitch = val
        self.save_audio_settings()
        
    def save_audio_settings(self):
        queries.save_global_settings(self.controller)

    # --- PLAYLIST ACTIONS ---
    def toggle_album(self, album):
        if album in self.controller.active_albums:
            self.controller.active_albums.remove(album)
        else:
            self.controller.active_albums.append(album)
            
        self.controller.save_active_albums()
        self.controller.build_playlist()
        self.refresh_ui()

    def handle_events(self, events):
        for event in events:
            for el in self.elements:
                el.handle_event(event)
            self.additional_events(event)

    def additional_events(self, event):
        mx, my = pygame.mouse.get_pos()
        
        # Scrolling
        if event.type == pygame.MOUSEWHEEL:
            if mx < c.MUSIC_LEFT_PANE_W:
                self.album_scroll_y += event.y * 30
                self.album_scroll_y = min(0, self.album_scroll_y)
            else:
                self.track_scroll_y += event.y * 30
                self.track_scroll_y = min(0, self.track_scroll_y)
            self.refresh_ui()
            
    def additional_draw(self, surface):
        font_title = fonts.get("heading1")
        font_norm = fonts.get("normal")
        
        # Left Pane Background
        left_pane = pygame.Rect(0, 0, c.MUSIC_LEFT_PANE_W, c.SCREEN_HEIGHT)
        pygame.draw.rect(surface, (35, 35, 45), left_pane)
        pygame.draw.line(surface, (100, 100, 100), (c.MUSIC_LEFT_PANE_W, 0), (c.MUSIC_LEFT_PANE_W, c.SCREEN_HEIGHT), 2)
        
        # Top headers
        surface.blit(font_title.render("ALBUMS", True, (255, 255, 255)), (20, 80))
        
        np_text = f"Now Playing: {os.path.basename(self.controller.now_playing)}" if self.controller.now_playing != "None" else "Now Playing: Nothing"
        surface.blit(font_norm.render(np_text, True, (255, 215, 0)), (c.MUSIC_LEFT_PANE_W + 20, 30))

    def handle_back_key(self):
        self.next_state = getattr(self, 'return_state', 'MENU')
        self.done = True