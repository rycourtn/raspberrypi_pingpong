#!/usr/bin/env python3
"""
Ping Pong Scorer - Raspberry Pi Version
- Setup screen: clickable buttons
- Game screen: HTTP only for scoring (no touch scoring)
"""
import pygame
import threading
import socket
import requests

# Colors - Purple and Pink theme
C_P1_BG = (128, 0, 128)    # Purple
C_P2_BG = (255, 20, 147)   # Deep Pink
C_DARK = (30, 20, 40)      # Dark purple background
C_WHITE = (255, 255, 255)
C_GOLD = (255, 215, 0)
C_FLASH_P1 = (200, 150, 255)
C_FLASH_P2 = (255, 150, 200)
C_GREEN = (39, 174, 96)
C_ORANGE = (243, 156, 18)
C_GRAY = (80, 80, 80)

from flask import Flask, jsonify

# Player name options
PLAYER_NAMES = ["Ryan", "Ethan", "Ben", "Guest"]

# External replay server
REPLAY_SERVER = "http://192.168.1.175"

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

class PingPongDisplay:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.mouse.set_visible(True)
        
        # Load or create sounds
        self.setup_sounds()
        
        # Fullscreen on Pi
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.W, self.H = self.screen.get_size()
        pygame.display.set_caption("Ping Pong Scorer")
        
        # Game State
        self.p1_name = PLAYER_NAMES[0]
        self.p2_name = PLAYER_NAMES[1]
        self.p1_score = 0
        self.p2_score = 0
        self.serving = 1
        self.points_serve = 0
        self.game_started = False
        self.game_over = False
        
        # Game Settings
        self.points_to_win = 11
        self.serves_per_turn = 2
        
        # Selection indices
        self.p1_name_idx = 0
        self.p2_name_idx = 1
        self.first_server = 1  # 1 = Door serves first, 2 = Bong serves first
        
        # Flash animation
        self.flash_alpha_p1 = 0
        self.flash_alpha_p2 = 0
        
        # Replay state
        self.playing_replay = False
        self.replay_frames = []
        self.replay_frame_idx = 0
        self.replay_last_frame_time = 0
        self.replay_close_btn = None
        
        # Stream capture buffer (stores frames in RAM)
        self.stream_buffer = []
        self.stream_buffer_lock = threading.Lock()
        self.max_buffer_seconds = 180  # 3 minutes max per rally
        self.stream_capturing = False
        self.saved_replay_frames = []  # Saved replay from last rally
        self.capture_start_time = None  # Reset on each new rally
        
        # Fonts - scale based on screen size
        scale = self.H / 600
        self.font_score = pygame.font.Font(None, int(150 * scale))
        self.font_name = pygame.font.Font(None, int(40 * scale))
        self.font_serve = pygame.font.Font(None, int(30 * scale))
        self.font_title = pygame.font.Font(None, int(50 * scale))
        self.font_button = pygame.font.Font(None, int(35 * scale))
        self.font_small = pygame.font.Font(None, int(28 * scale))
        self.font_url = pygame.font.Font(None, int(45 * scale))
        
        # Get IP for display
        self.ip = get_ip()
        
        # Flask app
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_sounds(self):
        """Create simple beep sounds"""
        try:
            sample_rate = 22050
            # Score sound - short beep
            duration = 0.15
            frames = int(duration * sample_rate)
            freq = 880
            arr = bytes([int(128 + 100 * ((i * freq // sample_rate) % 2 * 2 - 1)) for i in range(frames)])
            self.sound_score = pygame.mixer.Sound(buffer=arr)
            self.sound_score.set_volume(0.5)
            
            # Win sound - longer tone
            duration = 0.4
            frames = int(duration * sample_rate)
            freq = 1200
            arr = bytes([int(128 + 100 * ((i * freq // sample_rate) % 2 * 2 - 1)) for i in range(frames)])
            self.sound_win = pygame.mixer.Sound(buffer=arr)
            self.sound_win.set_volume(0.6)
            
            self.sound_enabled = True
            print("Sound initialized")
        except Exception as e:
            print(f"Sound init failed: {e}")
            self.sound_enabled = False

    def play_sound(self, sound_type):
        if not self.sound_enabled:
            return
        try:
            if sound_type == 'score':
                self.sound_score.play()
            elif sound_type == 'win':
                self.sound_win.play()
        except:
            pass

    def send_to_replay_server(self, endpoint):
        """Send HTTP request to replay server in background"""
        def do_request():
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Connection": "keep-alive",
                    "Cache-Control": "max-age=0",
                    "Upgrade-Insecure-Requests": "1"
                }
                requests.get(f"{REPLAY_SERVER}/{endpoint}", headers=headers, timeout=30)
                print(f"Sent /{endpoint} to replay server", flush=True)
            except Exception as e:
                print(f"Failed to send /{endpoint}: {e}", flush=True)
        threading.Thread(target=do_request, daemon=True).start()

    def start_stream_capture(self):
        """Start capturing the live stream into RAM buffer"""
        import io
        import time
        
        def capture_loop():
            print("Starting stream capture...", flush=True)
            self.stream_capturing = True
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0",
                "Upgrade-Insecure-Requests": "1"
            }
            
            while self.stream_capturing:
                try:
                    response = requests.get(f"{REPLAY_SERVER}/stream", headers=headers, stream=True, timeout=30)
                    print(f"Connected to stream, status: {response.status_code}", flush=True)
                    
                    buffer = b''
                    for chunk in response.iter_content(chunk_size=4096):
                        if not self.stream_capturing:
                            break
                        
                        # Only capture if game is active and not over
                        if not self.game_started or self.game_over:
                            continue
                        
                        # Start timing when we begin capturing a new rally
                        if self.capture_start_time is None:
                            self.capture_start_time = time.time()
                        
                        # Stop after 3 minutes for this rally
                        if time.time() - self.capture_start_time > self.max_buffer_seconds:
                            continue
                        
                        if chunk:
                            buffer += chunk
                            
                            # Look for complete JPEG frames
                            while True:
                                start = buffer.find(b'\xff\xd8')
                                if start == -1:
                                    buffer = b''
                                    break
                                    
                                end = buffer.find(b'\xff\xd9', start)
                                if end == -1:
                                    # Keep data from start marker
                                    buffer = buffer[start:]
                                    break
                                
                                # Extract complete frame
                                jpg_data = buffer[start:end + 2]
                                buffer = buffer[end + 2:]
                                
                                # Convert to pygame surface
                                try:
                                    img_io = io.BytesIO(jpg_data)
                                    surface = pygame.image.load(img_io)
                                    surface = pygame.transform.scale(surface, (self.W, self.H))
                                    
                                    with self.stream_buffer_lock:
                                        self.stream_buffer.append(surface)
                                        if len(self.stream_buffer) % 100 == 0:
                                            print(f"Buffer: {len(self.stream_buffer)} frames, last frame size: {surface.get_size()}", flush=True)
                                except Exception as e:
                                    print(f"Frame load error: {e}", flush=True)
                                    
                except Exception as e:
                    print(f"Stream capture error: {e}", flush=True)
                    time.sleep(2)  # Wait before reconnecting
            
            print("Stream capture stopped", flush=True)
        
        threading.Thread(target=capture_loop, daemon=True).start()

    def trigger_replay(self):
        """Play the saved replay buffer"""
        print("Replay button pressed", flush=True)
        
        if not self.saved_replay_frames:
            print("No saved replay available!", flush=True)
            return
        
        self.replay_frames = self.saved_replay_frames.copy()
        print(f"Playing {len(self.replay_frames)} frames", flush=True)
        
        self.replay_frame_idx = 0
        self.replay_last_frame_time = pygame.time.get_ticks()
        self.playing_replay = True

    def save_replay_buffer(self):
        """Save current buffer as replay and clear for next rally"""
        with self.stream_buffer_lock:
            if self.stream_buffer:
                self.saved_replay_frames = self.stream_buffer.copy()
                print(f"Saved {len(self.saved_replay_frames)} frames for replay", flush=True)
                self.stream_buffer = []
            else:
                print("No frames to save", flush=True)
        # Reset timer for next rally
        self.capture_start_time = None

    def stop_replay(self):
        """Stop replay and return to game"""
        self.playing_replay = False
        self.replay_frames = []
        self.replay_frame_idx = 0
        print("Replay stopped", flush=True)

    def setup_routes(self):
        @self.app.route('/score/player1', methods=['GET', 'POST'])
        def s1():
            # Save current buffer for replay, then clear it
            self.save_replay_buffer()
            self.score(2)  # Button 1 scores for Player 2
            return jsonify(status='ok', player=self.p2_name, score=self.p2_score)
        
        @self.app.route('/score/player2', methods=['GET', 'POST'])
        def s2():
            # Save current buffer for replay, then clear it
            self.save_replay_buffer()
            self.score(1)  # Button 2 scores for Player 1
            return jsonify(status='ok', player=self.p1_name, score=self.p1_score)
            
        @self.app.route('/reset', methods=['GET', 'POST'])
        def r():
            self.reset_game()
            return jsonify(status='ok')
        
        @self.app.route('/status', methods=['GET'])
        def status():
            return jsonify(
                p1_name=self.p1_name,
                p1_score=self.p1_score,
                p2_name=self.p2_name, 
                p2_score=self.p2_score,
                serving=self.serving,
                game_started=self.game_started,
                game_over=self.game_over
            )

        @self.app.route('/')
        def remote():
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ display:flex; flex-direction:column; margin:0; height:100vh; background:#1e1428; font-family:Arial; }}
                    h1 {{ color:white; text-align:center; padding:20px; margin:0; }}
                    .buttons {{ display:flex; flex:1; gap:10px; padding:10px; }}
                    .btn {{ flex:1; border:none; border-radius:15px; font-size:28px; font-weight:bold; color:white; cursor:pointer; }}
                    .btn:active {{ opacity:0.7; transform:scale(0.98); }}
                    .p1 {{ background:#800080; }}
                    .p2 {{ background:#ff1493; }}
                    .reset {{ background:#f39c12; margin:10px; padding:20px; border-radius:10px; }}
                    .status {{ color:#bdc3c7; text-align:center; padding:15px; font-size:18px; }}
                </style>
            </head>
            <body>
                <h1>🏓 Ping Pong Remote</h1>
                <div class="buttons">
                    <button class="btn p1" onclick="score(1)">{self.p1_name}</button>
                    <button class="btn p2" onclick="score(2)">{self.p2_name}</button>
                </div>
                <button class="btn reset" onclick="reset()">Reset Game</button>
                <div class="status" id="status">Tap player to score</div>
                <script>
                    function score(p) {{ 
                        fetch('/score/player'+p, {{method:'POST'}})
                            .then(r=>r.json())
                            .then(d=>document.getElementById('status').textContent=d.player+': '+d.score); 
                    }}
                    function reset() {{ 
                        fetch('/reset', {{method:'POST'}})
                            .then(()=>document.getElementById('status').textContent='Game reset!'); 
                    }}
                </script>
            </body>
            </html>
            '''

    def start_flask(self):
        t = threading.Thread(
            target=lambda: self.app.run(host='0.0.0.0', port=5000, use_reloader=False, threaded=True), 
            daemon=True
        )
        t.start()

    def score(self, player):
        if self.game_over or not self.game_started:
            return
        
        if player == 1:
            self.p1_score += 1
            self.flash_alpha_p1 = 255
        else:
            self.p2_score += 1
            self.flash_alpha_p2 = 255
        
        self.play_sound('score')
            
        print(f"{self.p1_name if player == 1 else self.p2_name} scored! {self.p1_score}-{self.p2_score}")
        
        # Serve Logic
        self.points_serve += 1
        deuce = (self.p1_score >= self.points_to_win - 1 and self.p2_score >= self.points_to_win - 1)
        threshold = 1 if deuce else self.serves_per_turn
        if self.points_serve >= threshold:
            self.serving = 2 if self.serving == 1 else 1
            self.points_serve = 0
            
        # Win Logic
        if (self.p1_score >= self.points_to_win or self.p2_score >= self.points_to_win) and abs(self.p1_score - self.p2_score) >= 2:
            self.game_over = True
            self.play_sound('win')
            winner = self.p1_name if self.p1_score > self.p2_score else self.p2_name
            print(f"Game Over! {winner} wins!")

    def reset_game(self):
        self.p1_score = 0
        self.p2_score = 0
        self.serving = self.first_server
        self.points_serve = 0
        self.game_over = False
        
        # Clear the stream buffer for new game
        with self.stream_buffer_lock:
            self.stream_buffer = []
        
        print("Game reset!", flush=True)

    def start_game(self):
        self.p1_name = PLAYER_NAMES[self.p1_name_idx]
        self.p2_name = PLAYER_NAMES[self.p2_name_idx]
        self.game_started = True
        self.reset_game()
        
        # Start capturing the stream
        if not self.stream_capturing:
            self.start_stream_capture()

    def draw_button(self, rect, text, color, text_color=C_WHITE, selected=False):
        if selected:
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
        else:
            pygame.draw.rect(self.screen, C_GRAY, rect, border_radius=8)
            pygame.draw.rect(self.screen, color, rect, 3, border_radius=8)
        
        txt = self.font_button.render(text, True, text_color if selected else color)
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
        return rect

    def draw_setup(self):
        self.screen.fill(C_DARK)
        
        # Title
        title = self.font_title.render("PING PONG SCORER", True, C_WHITE)
        self.screen.blit(title, (self.W//2 - title.get_width()//2, 20))
        
        self.setup_buttons = {}
        
        btn_w = int(self.W * 0.12)
        btn_h = int(self.H * 0.08)
        spacing = int(self.W * 0.015)
        left_margin = int(self.W * 0.08)
        btn_start_x = int(self.W * 0.25)
        
        # Player 1 Selection
        y = int(self.H * 0.15)
        p1_label = self.font_name.render("Door:", True, C_P1_BG)
        self.screen.blit(p1_label, (left_margin, y + btn_h//3))
        
        for i, name in enumerate(PLAYER_NAMES):
            x = btn_start_x + i * (btn_w + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.draw_button(rect, name, C_P1_BG, selected=(i == self.p1_name_idx))
            self.setup_buttons[f"p1_{i}"] = rect
        
        # Player 2 Selection
        y = int(self.H * 0.27)
        p2_label = self.font_name.render("Bong:", True, C_P2_BG)
        self.screen.blit(p2_label, (left_margin, y + btn_h//3))
        
        for i, name in enumerate(PLAYER_NAMES):
            x = btn_start_x + i * (btn_w + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.draw_button(rect, name, C_P2_BG, selected=(i == self.p2_name_idx))
            self.setup_buttons[f"p2_{i}"] = rect
        
        # Serve First checkbox (next to Guest for Player 2)
        guest_idx = PLAYER_NAMES.index("Guest")
        checkbox_x = btn_start_x + guest_idx * (btn_w + spacing) + btn_w + spacing
        checkbox_size = int(btn_h * 0.6)
        checkbox_y = y + (btn_h - checkbox_size) // 2
        checkbox_rect = pygame.Rect(checkbox_x, checkbox_y, checkbox_size, checkbox_size)
        
        # Draw checkbox border
        pygame.draw.rect(self.screen, C_GOLD, checkbox_rect, 3, border_radius=4)
        # Fill if Bong serves first
        if self.first_server == 2:
            inner_rect = checkbox_rect.inflate(-8, -8)
            pygame.draw.rect(self.screen, C_GOLD, inner_rect, border_radius=2)
        
        # Label for checkbox
        serve_label = self.font_small.render("Serves First", True, C_GOLD)
        self.screen.blit(serve_label, (checkbox_x + checkbox_size + 8, checkbox_y + (checkbox_size - serve_label.get_height()) // 2))
        self.setup_buttons["serve_first_p2"] = checkbox_rect
        
        # Also add checkbox for Player 1 (Door)
        y_p1 = int(self.H * 0.15)
        checkbox_rect_p1 = pygame.Rect(checkbox_x, y_p1 + (btn_h - checkbox_size) // 2, checkbox_size, checkbox_size)
        pygame.draw.rect(self.screen, C_GOLD, checkbox_rect_p1, 3, border_radius=4)
        if self.first_server == 1:
            inner_rect = checkbox_rect_p1.inflate(-8, -8)
            pygame.draw.rect(self.screen, C_GOLD, inner_rect, border_radius=2)
        serve_label_p1 = self.font_small.render("Serves First", True, C_GOLD)
        self.screen.blit(serve_label_p1, (checkbox_x + checkbox_size + 8, y_p1 + (btn_h - serve_label_p1.get_height()) // 2))
        self.setup_buttons["serve_first_p1"] = checkbox_rect_p1
        
        # Points to Win
        y = int(self.H * 0.42)
        pts_label = self.font_name.render("Points:", True, C_GOLD)
        self.screen.blit(pts_label, (left_margin, y + btn_h//3))
        
        for i, pts in enumerate([7, 11, 21]):
            x = btn_start_x + i * (btn_w + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.draw_button(rect, str(pts), C_GOLD, C_DARK, selected=(self.points_to_win == pts))
            self.setup_buttons[f"pts_{pts}"] = rect
        
        # Serves per Turn
        y = int(self.H * 0.54)
        srv_label = self.font_name.render("Serves:", True, C_GOLD)
        self.screen.blit(srv_label, (left_margin, y + btn_h//3))
        
        for i, srv in enumerate([1, 2, 5]):
            x = btn_start_x + i * (btn_w + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.draw_button(rect, str(srv), C_GOLD, C_DARK, selected=(self.serves_per_turn == srv))
            self.setup_buttons[f"srv_{srv}"] = rect
        
        # Start Button
        start_w = int(self.W * 0.35)
        start_h = int(self.H * 0.12)
        start_rect = pygame.Rect(self.W//2 - start_w//2, int(self.H * 0.68), start_w, start_h)
        pygame.draw.rect(self.screen, C_GREEN, start_rect, border_radius=15)
        start_text = self.font_title.render("START GAME", True, C_WHITE)
        self.screen.blit(start_text, (start_rect.centerx - start_text.get_width()//2, 
                                      start_rect.centery - start_text.get_height()//2))
        self.setup_buttons["start"] = start_rect

    def draw_game(self):
        # Check if playing replay
        if self.playing_replay and self.replay_frames:
            current_time = pygame.time.get_ticks()
            # Play at ~30fps (33ms per frame)
            if current_time - self.replay_last_frame_time > 33:
                self.replay_frame_idx += 1
                self.replay_last_frame_time = current_time
                
                if self.replay_frame_idx >= len(self.replay_frames):
                    # Replay finished - loop back to start
                    self.replay_frame_idx = 0
            
            # Draw current frame
            if self.replay_frame_idx < len(self.replay_frames):
                self.screen.blit(self.replay_frames[self.replay_frame_idx], (0, 0))
                
                # Draw "REPLAY" text overlay
                replay_text = self.font_title.render("▶ REPLAY", True, C_GOLD)
                self.screen.blit(replay_text, (20, 20))
                
                # Draw close button (top right)
                btn_w = int(self.W * 0.1)
                btn_h = int(self.H * 0.06)
                close_rect = pygame.Rect(self.W - btn_w - 20, 20, btn_w, btn_h)
                pygame.draw.rect(self.screen, (200, 50, 50), close_rect, border_radius=5)
                close_txt = self.font_small.render("CLOSE", True, C_WHITE)
                self.screen.blit(close_txt, (close_rect.centerx - close_txt.get_width()//2, close_rect.centery - close_txt.get_height()//2))
                self.replay_close_btn = close_rect
            return
        
        self.replay_close_btn = None
        
        # Left half (P1) - Purple
        pygame.draw.rect(self.screen, C_P1_BG, (0, 0, self.W//2, self.H))
        # Right half (P2) - Pink
        pygame.draw.rect(self.screen, C_P2_BG, (self.W//2, 0, self.W//2, self.H))
        
        center_p1 = self.W // 4
        center_p2 = (self.W // 4) * 3
        
        # Names
        n1 = self.font_name.render(self.p1_name.upper(), True, C_WHITE)
        self.screen.blit(n1, (center_p1 - n1.get_width()//2, int(self.H * 0.08)))
        
        n2 = self.font_name.render(self.p2_name.upper(), True, C_WHITE)
        self.screen.blit(n2, (center_p2 - n2.get_width()//2, int(self.H * 0.08)))
        
        # Scores
        score_color_p1 = C_GOLD if self.game_over and self.p1_score > self.p2_score else C_WHITE
        score_color_p2 = C_GOLD if self.game_over and self.p2_score > self.p1_score else C_WHITE
        
        s1 = self.font_score.render(str(self.p1_score), True, score_color_p1)
        self.screen.blit(s1, (center_p1 - s1.get_width()//2, self.H//2 - s1.get_height()//2))
        
        s2 = self.font_score.render(str(self.p2_score), True, score_color_p2)
        self.screen.blit(s2, (center_p2 - s2.get_width()//2, self.H//2 - s2.get_height()//2))
        
        # Serve indicator
        if not self.game_over:
            serve_text = self.font_serve.render("● SERVING", True, C_GOLD)
            if self.serving == 1:
                self.screen.blit(serve_text, (center_p1 - serve_text.get_width()//2, int(self.H * 0.78)))
            else:
                self.screen.blit(serve_text, (center_p2 - serve_text.get_width()//2, int(self.H * 0.78)))
        else:
            winner = self.p1_name if self.p1_score > self.p2_score else self.p2_name
            win_text = self.font_title.render(f"🏆 {winner} WINS! 🏆", True, C_GOLD)
            self.screen.blit(win_text, (self.W//2 - win_text.get_width()//2, int(self.H * 0.78)))
        
        # Flash effects
        if self.flash_alpha_p1 > 0:
            flash_surface = pygame.Surface((self.W//2, self.H))
            flash_surface.fill(C_FLASH_P1)
            flash_surface.set_alpha(self.flash_alpha_p1)
            self.screen.blit(flash_surface, (0, 0))
            self.flash_alpha_p1 = max(0, self.flash_alpha_p1 - 12)
            
        if self.flash_alpha_p2 > 0:
            flash_surface = pygame.Surface((self.W//2, self.H))
            flash_surface.fill(C_FLASH_P2)
            flash_surface.set_alpha(self.flash_alpha_p2)
            self.screen.blit(flash_surface, (self.W//2, 0))
            self.flash_alpha_p2 = max(0, self.flash_alpha_p2 - 12)
        
        # Store buttons for click handling
        self.game_buttons = {}
        
        # New Game button (small, top corner)
        btn_w = int(self.W * 0.12)
        btn_h = int(self.H * 0.06)
        new_rect = pygame.Rect(self.W - btn_w - 10, 10, btn_w, btn_h)
        pygame.draw.rect(self.screen, C_ORANGE, new_rect, border_radius=5)
        new_txt = self.font_small.render("NEW GAME", True, C_WHITE)
        self.screen.blit(new_txt, (new_rect.centerx - new_txt.get_width()//2, new_rect.centery - new_txt.get_height()//2))
        self.game_buttons["new_game"] = new_rect
        
        # Replay button (bottom center)
        replay_w = int(self.W * 0.15)
        replay_h = int(self.H * 0.08)
        replay_rect = pygame.Rect(self.W//2 - replay_w//2, int(self.H * 0.88), replay_w, replay_h)
        pygame.draw.rect(self.screen, C_GREEN, replay_rect, border_radius=8)
        replay_txt = self.font_button.render("REPLAY", True, C_WHITE)
        self.screen.blit(replay_txt, (replay_rect.centerx - replay_txt.get_width()//2, replay_rect.centery - replay_txt.get_height()//2))
        self.game_buttons["replay"] = replay_rect

    def handle_setup_click(self, pos):
        for key, rect in self.setup_buttons.items():
            if rect.collidepoint(pos):
                if key.startswith("p1_"):
                    self.p1_name_idx = int(key.split("_")[1])
                elif key.startswith("p2_"):
                    self.p2_name_idx = int(key.split("_")[1])
                elif key.startswith("pts_"):
                    self.points_to_win = int(key.split("_")[1])
                elif key.startswith("srv_"):
                    self.serves_per_turn = int(key.split("_")[1])
                elif key == "serve_first_p1":
                    self.first_server = 1
                elif key == "serve_first_p2":
                    self.first_server = 2
                elif key == "start":
                    self.start_game()
                return

    def handle_game_click(self, pos):
        # Check for replay close button first
        if self.playing_replay and self.replay_close_btn and self.replay_close_btn.collidepoint(pos):
            self.stop_replay()
            return
        
        # Only handle New Game and Replay buttons - no tap-to-score
        for key, rect in self.game_buttons.items():
            if rect.collidepoint(pos):
                if key == "new_game":
                    self.game_started = False
                    self.game_over = False
                elif key == "replay":
                    self.trigger_replay()
                return

    def run(self):
        # Start Flask server
        self.start_flask()
        
        clock = pygame.time.Clock()
        running = True
        
        print(f"\n🏓 Ping Pong Scorer Running!")
        print(f"📱 Remote Control: http://{self.ip}:5000")
        print(f"   Score P1: http://{self.ip}:5000/score/player1")
        print(f"   Score P2: http://{self.ip}:5000/score/player2")
        print()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_started:
                        self.handle_game_click(event.pos)
                    else:
                        self.handle_setup_click(event.pos)
                        
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()

            # Draw
            if self.game_started:
                self.draw_game()
            else:
                self.draw_setup()
                
            pygame.display.flip()
            clock.tick(60)
            
        pygame.quit()

if __name__ == "__main__":
    game = PingPongDisplay()
    game.run()