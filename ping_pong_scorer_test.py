#!/usr/bin/env python3
"""
Ping Pong Scorer - Pygame Display Version
All touch/click controls - no keyboard needed during game
"""
import pygame
import threading

# Colors - Purple and Pink theme
C_P1_BG = (128, 0, 128)    # Purple
C_P2_BG = (255, 20, 147)   # Deep Pink
C_DARK = (30, 20, 40)      # Dark purple background
C_WHITE = (255, 255, 255)
C_GOLD = (255, 215, 0)
C_FLASH_P1 = (200, 150, 255)  # Light purple flash
C_FLASH_P2 = (255, 150, 200)  # Light pink flash
C_GREEN = (39, 174, 96)
C_ORANGE = (243, 156, 18)
C_GRAY = (80, 80, 80)

try:
    from flask import Flask, jsonify
    FLASK_ENABLED = True
except ImportError:
    FLASK_ENABLED = False
    print("Flask not available - HTTP disabled")

# Player name options
PLAYER_NAMES = ["Ryan", "Ethan", "Ben", "Guest"]

class PingPongDisplay:
    def __init__(self):
        pygame.init()
        
        # Setup Screen
        self.W, self.H = 800, 600
        self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
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
        
        # Flash animation
        self.flash_alpha_p1 = 0
        self.flash_alpha_p2 = 0
        
        # Fonts
        self.font_score = pygame.font.Font(None, 150)
        self.font_name = pygame.font.Font(None, 40)
        self.font_serve = pygame.font.Font(None, 30)
        self.font_title = pygame.font.Font(None, 50)
        self.font_button = pygame.font.Font(None, 35)
        self.font_small = pygame.font.Font(None, 28)
        
        # Web Server
        if FLASK_ENABLED:
            self.app = Flask(__name__)
            self.setup_routes()
            self.start_flask()

    def setup_routes(self):
        @self.app.route('/score/player1', methods=['GET', 'POST'])
        def s1():
            self.score(1)
            return jsonify(status='ok', score=self.p1_score)
        
        @self.app.route('/score/player2', methods=['GET', 'POST'])
        def s2():
            self.score(2)
            return jsonify(status='ok', score=self.p2_score)
            
        @self.app.route('/reset', methods=['GET', 'POST'])
        def r():
            self.reset_game()
            return jsonify(status='ok')
        
        @self.app.route('/status', methods=['GET'])
        def status():
            return jsonify(
                p1_score=self.p1_score, 
                p2_score=self.p2_score,
                serving=self.serving,
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
                    .btn {{ flex:1; border:none; border-radius:15px; font-size:24px; font-weight:bold; color:white; cursor:pointer; }}
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
                            .then(d=>document.getElementById('status').textContent='Score: '+d.score); 
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
            target=lambda: self.app.run(host='0.0.0.0', port=8080, use_reloader=False, threaded=True), 
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
            
        print(f"{'P1' if player == 1 else 'P2'} scored! {self.p1_score}-{self.p2_score}")
        
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
            winner = self.p1_name if self.p1_score > self.p2_score else self.p2_name
            print(f"Game Over! {winner} wins!")

    def reset_game(self):
        self.p1_score = 0
        self.p2_score = 0
        self.serving = 1
        self.points_serve = 0
        self.game_over = False
        print("Game reset!")

    def start_game(self):
        self.p1_name = PLAYER_NAMES[self.p1_name_idx]
        self.p2_name = PLAYER_NAMES[self.p2_name_idx]
        self.game_started = True
        self.reset_game()

    def draw_button(self, rect, text, color, text_color=C_WHITE, selected=False):
        """Draw a clickable button"""
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
        
        # Store button rects for click detection
        self.setup_buttons = {}
        
        btn_w = 120
        btn_h = 50
        spacing = 10
        
        # Player 1 Selection
        y = 90
        p1_label = self.font_name.render("Player 1:", True, C_P1_BG)
        self.screen.blit(p1_label, (50, y + 10))
        
        for i, name in enumerate(PLAYER_NAMES):
            x = 200 + i * (btn_w + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.draw_button(rect, name, C_P1_BG, selected=(i == self.p1_name_idx))
            self.setup_buttons[f"p1_{i}"] = rect
        
        # Player 2 Selection
        y = 160
        p2_label = self.font_name.render("Player 2:", True, C_P2_BG)
        self.screen.blit(p2_label, (50, y + 10))
        
        for i, name in enumerate(PLAYER_NAMES):
            x = 200 + i * (btn_w + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.draw_button(rect, name, C_P2_BG, selected=(i == self.p2_name_idx))
            self.setup_buttons[f"p2_{i}"] = rect
        
        # Points to Win
        y = 250
        pts_label = self.font_name.render("Points to Win:", True, C_GOLD)
        self.screen.blit(pts_label, (50, y + 10))
        
        for i, pts in enumerate([7, 11, 21]):
            x = 250 + i * (btn_w + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.draw_button(rect, str(pts), C_GOLD, C_DARK, selected=(self.points_to_win == pts))
            self.setup_buttons[f"pts_{pts}"] = rect
        
        # Serves per Turn
        y = 320
        srv_label = self.font_name.render("Serves/Turn:", True, C_GOLD)
        self.screen.blit(srv_label, (50, y + 10))
        
        for i, srv in enumerate([1, 2, 5]):
            x = 250 + i * (btn_w + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.draw_button(rect, str(srv), C_GOLD, C_DARK, selected=(self.serves_per_turn == srv))
            self.setup_buttons[f"srv_{srv}"] = rect
        
        # Start Button
        start_rect = pygame.Rect(self.W//2 - 150, 410, 300, 80)
        pygame.draw.rect(self.screen, C_GREEN, start_rect, border_radius=15)
        start_text = self.font_title.render("START GAME", True, C_WHITE)
        self.screen.blit(start_text, (start_rect.centerx - start_text.get_width()//2, 
                                      start_rect.centery - start_text.get_height()//2))
        self.setup_buttons["start"] = start_rect
        
        # Preview
        preview = self.font_small.render(f"{PLAYER_NAMES[self.p1_name_idx]} vs {PLAYER_NAMES[self.p2_name_idx]} • First to {self.points_to_win} • {self.serves_per_turn} serve(s)/turn", True, (150, 150, 150))
        self.screen.blit(preview, (self.W//2 - preview.get_width()//2, 510))
        
        if FLASK_ENABLED:
            url = self.font_small.render("Remote: http://localhost:8080", True, C_GOLD)
            self.screen.blit(url, (self.W//2 - url.get_width()//2, 550))

    def draw_game(self):
        # Score areas (clickable)
        self.game_buttons = {}
        
        # Left half (P1) - Purple - CLICKABLE TO SCORE
        p1_rect = pygame.Rect(0, 0, self.W//2, self.H - 80)
        pygame.draw.rect(self.screen, C_P1_BG, p1_rect)
        self.game_buttons["score_p1"] = p1_rect
        
        # Right half (P2) - Pink - CLICKABLE TO SCORE
        p2_rect = pygame.Rect(self.W//2, 0, self.W//2, self.H - 80)
        pygame.draw.rect(self.screen, C_P2_BG, p2_rect)
        self.game_buttons["score_p2"] = p2_rect
        
        center_p1 = self.W // 4
        center_p2 = (self.W // 4) * 3
        
        # Names
        n1 = self.font_name.render(self.p1_name.upper(), True, C_WHITE)
        self.screen.blit(n1, (center_p1 - n1.get_width()//2, 30))
        
        n2 = self.font_name.render(self.p2_name.upper(), True, C_WHITE)
        self.screen.blit(n2, (center_p2 - n2.get_width()//2, 30))
        
        # Tap hint
        tap1 = self.font_small.render("TAP TO SCORE", True, (200, 180, 220))
        self.screen.blit(tap1, (center_p1 - tap1.get_width()//2, 70))
        
        tap2 = self.font_small.render("TAP TO SCORE", True, (255, 180, 200))
        self.screen.blit(tap2, (center_p2 - tap2.get_width()//2, 70))
        
        # Scores
        score_color_p1 = C_GOLD if self.game_over and self.p1_score > self.p2_score else C_WHITE
        score_color_p2 = C_GOLD if self.game_over and self.p2_score > self.p1_score else C_WHITE
        
        s1 = self.font_score.render(str(self.p1_score), True, score_color_p1)
        self.screen.blit(s1, (center_p1 - s1.get_width()//2, self.H//2 - s1.get_height()//2 - 20))
        
        s2 = self.font_score.render(str(self.p2_score), True, score_color_p2)
        self.screen.blit(s2, (center_p2 - s2.get_width()//2, self.H//2 - s2.get_height()//2 - 20))
        
        # Serve indicator
        if not self.game_over:
            serve_text = self.font_serve.render("● SERVING", True, C_GOLD)
            if self.serving == 1:
                self.screen.blit(serve_text, (center_p1 - serve_text.get_width()//2, self.H - 130))
            else:
                self.screen.blit(serve_text, (center_p2 - serve_text.get_width()//2, self.H - 130))
        
        # Flash effects
        if self.flash_alpha_p1 > 0:
            flash_surface = pygame.Surface((self.W//2, self.H - 80))
            flash_surface.fill(C_FLASH_P1)
            flash_surface.set_alpha(self.flash_alpha_p1)
            self.screen.blit(flash_surface, (0, 0))
            self.flash_alpha_p1 = max(0, self.flash_alpha_p1 - 15)
            
        if self.flash_alpha_p2 > 0:
            flash_surface = pygame.Surface((self.W//2, self.H - 80))
            flash_surface.fill(C_FLASH_P2)
            flash_surface.set_alpha(self.flash_alpha_p2)
            self.screen.blit(flash_surface, (self.W//2, 0))
            self.flash_alpha_p2 = max(0, self.flash_alpha_p2 - 15)
        
        # Bottom control bar
        pygame.draw.rect(self.screen, C_DARK, (0, self.H - 80, self.W, 80))
        
        # Control buttons
        btn_w = 150
        btn_h = 50
        y = self.H - 65
        
        if self.game_over:
            # Winner message
            winner = self.p1_name if self.p1_score > self.p2_score else self.p2_name
            win_text = self.font_name.render(f"🏆 {winner} WINS! 🏆", True, C_GOLD)
            self.screen.blit(win_text, (self.W//2 - win_text.get_width()//2, y - 10))
        
        # Reset button
        reset_rect = pygame.Rect(20, y, btn_w, btn_h)
        pygame.draw.rect(self.screen, C_ORANGE, reset_rect, border_radius=8)
        reset_txt = self.font_button.render("RESET", True, C_WHITE)
        self.screen.blit(reset_txt, (reset_rect.centerx - reset_txt.get_width()//2, reset_rect.centery - reset_txt.get_height()//2))
        self.game_buttons["reset"] = reset_rect
        
        # New Game button
        new_rect = pygame.Rect(self.W - 170, y, btn_w, btn_h)
        pygame.draw.rect(self.screen, C_P1_BG, new_rect, border_radius=8)
        new_txt = self.font_button.render("NEW GAME", True, C_WHITE)
        self.screen.blit(new_txt, (new_rect.centerx - new_txt.get_width()//2, new_rect.centery - new_txt.get_height()//2))
        self.game_buttons["new_game"] = new_rect
        
        # Game info
        info = self.font_small.render(f"First to {self.points_to_win}", True, (150, 150, 150))
        self.screen.blit(info, (self.W//2 - info.get_width()//2, y + 10))

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
                elif key == "start":
                    self.start_game()
                return

    def handle_game_click(self, pos):
        for key, rect in self.game_buttons.items():
            if rect.collidepoint(pos):
                if key == "score_p1" and not self.game_over:
                    self.score(1)
                elif key == "score_p2" and not self.game_over:
                    self.score(2)
                elif key == "reset":
                    self.reset_game()
                elif key == "new_game":
                    self.game_started = False
                    self.game_over = False
                return

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        print("\n🏓 Ping Pong Scorer - TOUCH/CLICK MODE")
        print("All controls are clickable buttons!")
        if FLASK_ENABLED:
            print("Remote: http://localhost:8080")
        print()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.VIDEORESIZE:
                    self.W, self.H = event.w, event.h
                    self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_started:
                        self.handle_game_click(event.pos)
                    else:
                        self.handle_setup_click(event.pos)
                        
                elif event.type == pygame.KEYDOWN:
                    # Keyboard shortcuts still work
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    elif self.game_started:
                        if event.key == pygame.K_a:
                            self.score(1)
                        elif event.key == pygame.K_l:
                            self.score(2)
                        elif event.key == pygame.K_r:
                            self.reset_game()
                        elif event.key == pygame.K_n:
                            self.game_started = False
                            self.game_over = False

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