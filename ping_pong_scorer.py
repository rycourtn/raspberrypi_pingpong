#!/usr/bin/env python3
"""
Ping Pong Scoring System for Raspberry Pi
- HTTP endpoints for scoring via ESP32/webhook
- GUI display for VNC Viewer
- Player selection and serving tracking
- Sound effects for scoring
"""

import tkinter as tk
from tkinter import messagebox
import pygame
import threading
import time
from flask import Flask, jsonify

class PingPongScorer:
    def __init__(self):
        # Initialize pygame for sound
        try:
            pygame.mixer.init()
            self.sound_enabled = True
        except:
            print("Sound not available")
            self.sound_enabled = False
        
        # Game state
        self.player1_name = "Player 1"
        self.player2_name = "Player 2"
        self.player1_score = 0
        self.player2_score = 0
        self.serving_player = 1
        self.game_started = False
        self.game_over = False
        self.points_to_serve = 0
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Ping Pong Scorer")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        self.root.attributes('-fullscreen', True)
        
        # Flask app for HTTP endpoints
        self.app = Flask(__name__)
        self.setup_routes()
        
        self.setup_gui()
        
    def setup_routes(self):
        """Setup HTTP endpoints for ESP32"""
        @self.app.route('/score/player1', methods=['GET', 'POST'])
        def score_player1():
            if self.game_started and not self.game_over:
                self.root.after(0, self.player1_scored)
                return jsonify({"status": "ok", "player": self.player1_name, "score": self.player1_score + 1})
            return jsonify({"status": "error", "message": "Game not active"})
        
        @self.app.route('/score/player2', methods=['GET', 'POST'])
        def score_player2():
            if self.game_started and not self.game_over:
                self.root.after(0, self.player2_scored)
                return jsonify({"status": "ok", "player": self.player2_name, "score": self.player2_score + 1})
            return jsonify({"status": "error", "message": "Game not active"})
        
        @self.app.route('/status', methods=['GET'])
        def get_status():
            return jsonify({
                "player1": {"name": self.player1_name, "score": self.player1_score},
                "player2": {"name": self.player2_name, "score": self.player2_score},
                "serving": self.player1_name if self.serving_player == 1 else self.player2_name,
                "game_started": self.game_started,
                "game_over": self.game_over
            })
        
        @self.app.route('/reset', methods=['GET', 'POST'])
        def reset():
            self.root.after(0, self.reset_game)
            return jsonify({"status": "ok", "message": "Game reset"})
        
        @self.app.route('/', methods=['GET'])
        def control_page():
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Ping Pong Remote</title>
                <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{ font-family: Arial; background: #2c3e50; height: 100vh; display: flex; flex-direction: column; }}
                    h1 {{ color: #ecf0f1; text-align: center; padding: 20px; font-size: 24px; }}
                    .buttons {{ display: flex; flex: 1; gap: 10px; padding: 10px; }}
                    .score-btn {{ flex: 1; border: none; border-radius: 15px; font-size: 28px; font-weight: bold; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; }}
                    .score-btn:active {{ transform: scale(0.95); opacity: 0.8; }}
                    .p1 {{ background: #3498db; }}
                    .p2 {{ background: #e74c3c; }}
                    .reset {{ background: #f39c12; padding: 15px; margin: 10px; border-radius: 10px; font-size: 18px; }}
                    .status {{ color: #bdc3c7; text-align: center; padding: 10px; }}
                </style>
            </head>
            <body>
                <h1>🏓 Ping Pong Remote</h1>
                <div class="buttons">
                    <button class="score-btn p1" onclick="score(1)">{self.player1_name}</button>
                    <button class="score-btn p2" onclick="score(2)">{self.player2_name}</button>
                </div>
                <button class="score-btn reset" onclick="reset()">Reset Game</button>
                <div class="status" id="status">Tap a player to score</div>
                <script>
                    function score(player) {{
                        fetch('/score/player' + player, {{method: 'POST'}})
                            .then(r => r.json())
                            .then(d => document.getElementById('status').textContent = d.player + ': ' + d.score);
                    }}
                    function reset() {{
                        fetch('/reset', {{method: 'POST'}})
                            .then(() => document.getElementById('status').textContent = 'Game reset!');
                    }}
                </script>
            </body>
            </html>
            '''
        
    def setup_gui(self):
        """Setup the GUI interface"""
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_label = tk.Label(main_frame, text="🏓 PING PONG SCORER 🏓", 
                              font=('Arial', 24, 'bold'), fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=(0, 30))
        
        # Setup frame
        self.setup_frame = tk.Frame(main_frame, bg='#2c3e50')
        self.setup_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(self.setup_frame, text="Enter Player Names:", 
                font=('Arial', 18, 'bold'), fg='#ecf0f1', bg='#2c3e50').pack(pady=20)
        
        input_frame = tk.Frame(self.setup_frame, bg='#2c3e50')
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="Player 1:", font=('Arial', 14), 
                fg='#ecf0f1', bg='#2c3e50').grid(row=0, column=0, padx=10, pady=10)
        self.player1_entry = tk.Entry(input_frame, font=('Arial', 14), width=20)
        self.player1_entry.grid(row=0, column=1, padx=10, pady=10)
        self.player1_entry.insert(0, self.player1_name)
        
        tk.Label(input_frame, text="Player 2:", font=('Arial', 14), 
                fg='#ecf0f1', bg='#2c3e50').grid(row=1, column=0, padx=10, pady=10)
        self.player2_entry = tk.Entry(input_frame, font=('Arial', 14), width=20)
        self.player2_entry.grid(row=1, column=1, padx=10, pady=10)
        self.player2_entry.insert(0, self.player2_name)
        
        start_btn = tk.Button(self.setup_frame, text="START GAME", 
                             font=('Arial', 16, 'bold'), bg='#27ae60', fg='white',
                             command=self.start_game, padx=30, pady=15)
        start_btn.pack(pady=30)
        
        # URL info
        self.url_label = tk.Label(self.setup_frame, text="", 
                                 font=('Arial', 12), fg='#f39c12', bg='#2c3e50')
        self.url_label.pack(pady=10)
        
        # Game frame
        self.game_frame = tk.Frame(main_frame, bg='#2c3e50')
        
        score_frame = tk.Frame(self.game_frame, bg='#2c3e50')
        score_frame.pack(fill=tk.X, pady=30)
        
        p1_frame = tk.Frame(score_frame, bg='#3498db', relief=tk.RAISED, bd=3)
        p1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.player1_label = tk.Label(p1_frame, text=self.player1_name, 
                                     font=('Arial', 20, 'bold'), fg='white', bg='#3498db')
        self.player1_label.pack(pady=10)
        
        self.player1_score_label = tk.Label(p1_frame, text="0", 
                                           font=('Arial', 72, 'bold'), fg='white', bg='#3498db')
        self.player1_score_label.pack(pady=20)
        
        self.player1_serve_label = tk.Label(p1_frame, text="", 
                                           font=('Arial', 16, 'bold'), fg='#f1c40f', bg='#3498db')
        self.player1_serve_label.pack(pady=(0, 10))
        
        vs_label = tk.Label(score_frame, text="VS", font=('Arial', 24, 'bold'), 
                           fg='#ecf0f1', bg='#2c3e50')
        vs_label.pack(side=tk.LEFT, padx=20)
        
        p2_frame = tk.Frame(score_frame, bg='#e74c3c', relief=tk.RAISED, bd=3)
        p2_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.player2_label = tk.Label(p2_frame, text=self.player2_name, 
                                     font=('Arial', 20, 'bold'), fg='white', bg='#e74c3c')
        self.player2_label.pack(pady=10)
        
        self.player2_score_label = tk.Label(p2_frame, text="0", 
                                           font=('Arial', 72, 'bold'), fg='white', bg='#e74c3c')
        self.player2_score_label.pack(pady=20)
        
        self.player2_serve_label = tk.Label(p2_frame, text="", 
                                           font=('Arial', 16, 'bold'), fg='#f1c40f', bg='#e74c3c')
        self.player2_serve_label.pack(pady=(0, 10))
        
        controls_frame = tk.Frame(self.game_frame, bg='#2c3e50')
        controls_frame.pack(pady=30)
        
        reset_btn = tk.Button(controls_frame, text="RESET", font=('Arial', 14, 'bold'), 
                             bg='#f39c12', fg='white', command=self.reset_game, padx=20, pady=10)
        reset_btn.pack(side=tk.LEFT, padx=10)
        
        new_btn = tk.Button(controls_frame, text="NEW GAME", font=('Arial', 14, 'bold'), 
                           bg='#9b59b6', fg='white', command=self.new_game, padx=20, pady=10)
        new_btn.pack(side=tk.LEFT, padx=10)
        
        exit_btn = tk.Button(controls_frame, text="EXIT", font=('Arial', 14, 'bold'), 
                            bg='#e74c3c', fg='white', command=self.exit_app, padx=20, pady=10)
        exit_btn.pack(side=tk.LEFT, padx=10)
        
        self.game_url_label = tk.Label(self.game_frame, text="", 
                                       font=('Arial', 14, 'bold'), fg='#f39c12', bg='#2c3e50')
        self.game_url_label.pack(pady=20)

    def start_game(self):
        self.player1_name = self.player1_entry.get().strip() or "Player 1"
        self.player2_name = self.player2_entry.get().strip() or "Player 2"
        self.player1_label.config(text=self.player1_name)
        self.player2_label.config(text=self.player2_name)
        self.setup_frame.pack_forget()
        self.game_frame.pack(fill=tk.BOTH, expand=True)
        self.game_started = True
        self.serving_player = 1
        self.update_serve_display()
        self.play_sound('start')
        
    def player1_scored(self):
        if not self.game_started or self.game_over:
            return
        self.player1_score += 1
        self.points_to_serve += 1
        self.update_score_display()
        self.check_serve_change()
        self.check_game_over()
        self.play_sound('score')
        
    def player2_scored(self):
        if not self.game_started or self.game_over:
            return
        self.player2_score += 1
        self.points_to_serve += 1
        self.update_score_display()
        self.check_serve_change()
        self.check_game_over()
        self.play_sound('score')
        
    def update_score_display(self):
        self.player1_score_label.config(text=str(self.player1_score))
        self.player2_score_label.config(text=str(self.player2_score))
        
    def check_serve_change(self):
        if self.points_to_serve >= 2:
            self.serving_player = 2 if self.serving_player == 1 else 1
            self.points_to_serve = 0
            self.update_serve_display()
            
    def update_serve_display(self):
        if self.serving_player == 1:
            self.player1_serve_label.config(text="🏓 SERVING")
            self.player2_serve_label.config(text="")
        else:
            self.player1_serve_label.config(text="")
            self.player2_serve_label.config(text="🏓 SERVING")
            
    def check_game_over(self):
        if (self.player1_score >= 11 or self.player2_score >= 11):
            if abs(self.player1_score - self.player2_score) >= 2:
                self.game_over = True
                winner = self.player1_name if self.player1_score > self.player2_score else self.player2_name
                self.play_sound('win')
                messagebox.showinfo("Game Over!", f"🏆 {winner} Wins!\n\n{self.player1_name}: {self.player1_score}\n{self.player2_name}: {self.player2_score}")
                
    def play_sound(self, sound_type):
        if not self.sound_enabled:
            return
        try:
            if sound_type == 'score':
                self.create_beep(440, 0.1)
            elif sound_type == 'start':
                self.create_beep(523, 0.2)
            elif sound_type == 'win':
                for freq in [523, 659, 784]:
                    self.create_beep(freq, 0.2)
                    time.sleep(0.1)
        except:
            pass
            
    def create_beep(self, freq, duration):
        try:
            sample_rate = 22050
            frames = int(duration * sample_rate)
            arr = []
            for i in range(frames):
                wave = 4096 * (i % (sample_rate // freq) < (sample_rate // freq) // 2) - 2048
                arr.append([wave, wave])
            sound = pygame.sndarray.make_sound(pygame.array.array('h', arr))
            sound.play()
            time.sleep(duration)
        except:
            pass
            
    def reset_game(self):
        self.player1_score = 0
        self.player2_score = 0
        self.serving_player = 1
        self.points_to_serve = 0
        self.game_over = False
        self.update_score_display()
        self.update_serve_display()
        self.play_sound('start')
        
    def new_game(self):
        self.game_started = False
        self.game_over = False
        self.player1_score = 0
        self.player2_score = 0
        self.serving_player = 1
        self.points_to_serve = 0
        self.game_frame.pack_forget()
        self.setup_frame.pack(fill=tk.BOTH, expand=True)
        
    def exit_app(self):
        if self.sound_enabled:
            pygame.mixer.quit()
        self.root.quit()
        
    def get_ip(self):
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
        
    def run(self):
        ip = self.get_ip()
        url = f"http://{ip}:5000"
        self.url_label.config(text=f"📱 Remote Control: {url}")
        self.game_url_label.config(text=f"📱 Remote: {url}")
        
        # Start Flask in background thread
        flask_thread = threading.Thread(
            target=lambda: self.app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False), 
            daemon=True
        )
        flask_thread.start()
        
        print(f"\n🏓 Ping Pong Scorer Running!")
        print(f"📱 Remote: {url}")
        print(f"   Player 1: {url}/score/player1")
        print(f"   Player 2: {url}/score/player2\n")
        
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', True))
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.root.mainloop()

if __name__ == "__main__":
    app = PingPongScorer()
    app.run()