#!/usr/bin/env python3
"""
Ping Pong Scoring System - TEST VERSION
- Simulates GPIO buttons with keyboard keys
- Works on any computer for testing
- Press 'A' for Player 1, 'L' for Player 2
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pygame
import threading
import time
import os

class PingPongScorerTest:
    def __init__(self):
        # Initialize pygame for sound
        try:
            pygame.mixer.init()
            self.sound_enabled = True
        except:
            print("Sound not available - continuing without audio")
            self.sound_enabled = False
        
        # Game state
        self.player1_name = "Player 1"
        self.player2_name = "Player 2"
        self.player1_score = 0
        self.player2_score = 0
        self.serving_player = 1  # 1 or 2
        self.game_started = False
        self.game_over = False
        self.points_to_serve = 0  # Track points for serve changes
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Ping Pong Scorer - TEST MODE")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Don't start fullscreen in test mode
        # self.root.attributes('-fullscreen', True)
        
        self.setup_gui()
        self.setup_keyboard_bindings()
        
    def setup_gui(self):
        """Setup the GUI interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title with test mode indicator
        title_label = tk.Label(main_frame, text="🏓 PING PONG SCORER - TEST MODE 🏓", 
                              font=('Arial', 20, 'bold'), 
                              fg='#f39c12', bg='#2c3e50')
        title_label.pack(pady=(0, 10))
        
        # Test instructions
        test_info = tk.Label(main_frame, text="Press 'A' for Player 1 • Press 'L' for Player 2", 
                            font=('Arial', 12, 'bold'), 
                            fg='#e74c3c', bg='#2c3e50')
        test_info.pack(pady=(0, 20))
        
        # Player setup frame (shown before game starts)
        self.setup_frame = tk.Frame(main_frame, bg='#2c3e50')
        self.setup_frame.pack(fill=tk.BOTH, expand=True)
        
        # Player name inputs
        tk.Label(self.setup_frame, text="Enter Player Names:", 
                font=('Arial', 18, 'bold'), fg='#ecf0f1', bg='#2c3e50').pack(pady=20)
        
        input_frame = tk.Frame(self.setup_frame, bg='#2c3e50')
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="Player 1 (Press 'A'):", 
                font=('Arial', 14), fg='#ecf0f1', bg='#2c3e50').grid(row=0, column=0, padx=10, pady=10)
        self.player1_entry = tk.Entry(input_frame, font=('Arial', 14), width=20)
        self.player1_entry.grid(row=0, column=1, padx=10, pady=10)
        self.player1_entry.insert(0, self.player1_name)
        
        tk.Label(input_frame, text="Player 2 (Press 'L'):", 
                font=('Arial', 14), fg='#ecf0f1', bg='#2c3e50').grid(row=1, column=0, padx=10, pady=10)
        self.player2_entry = tk.Entry(input_frame, font=('Arial', 14), width=20)
        self.player2_entry.grid(row=1, column=1, padx=10, pady=10)
        self.player2_entry.insert(0, self.player2_name)
        
        # Start game button
        start_btn = tk.Button(self.setup_frame, text="START GAME", 
                             font=('Arial', 16, 'bold'), 
                             bg='#27ae60', fg='white',
                             command=self.start_game, 
                             padx=30, pady=15)
        start_btn.pack(pady=30)
        
        # Test buttons for clicking
        test_btn_frame = tk.Frame(self.setup_frame, bg='#2c3e50')
        test_btn_frame.pack(pady=20)
        
        tk.Label(test_btn_frame, text="Or click these test buttons:", 
                font=('Arial', 12), fg='#bdc3c7', bg='#2c3e50').pack(pady=(0, 10))
        
        test_p1_btn = tk.Button(test_btn_frame, text="Player 1 Score (A)", 
                               font=('Arial', 12), bg='#3498db', fg='white',
                               command=self.player1_scored_test, padx=20, pady=10)
        test_p1_btn.pack(side=tk.LEFT, padx=10)
        
        test_p2_btn = tk.Button(test_btn_frame, text="Player 2 Score (L)", 
                               font=('Arial', 12), bg='#e74c3c', fg='white',
                               command=self.player2_scored_test, padx=20, pady=10)
        test_p2_btn.pack(side=tk.LEFT, padx=10)
        
        # Game frame (shown during game)
        self.game_frame = tk.Frame(main_frame, bg='#2c3e50')
        
        # Score display
        score_frame = tk.Frame(self.game_frame, bg='#2c3e50')
        score_frame.pack(fill=tk.X, pady=30)
        
        # Player 1 score section
        p1_frame = tk.Frame(score_frame, bg='#3498db', relief=tk.RAISED, bd=3)
        p1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.player1_label = tk.Label(p1_frame, text=self.player1_name, 
                                     font=('Arial', 20, 'bold'), 
                                     fg='white', bg='#3498db')
        self.player1_label.pack(pady=10)
        
        self.player1_score_label = tk.Label(p1_frame, text="0", 
                                           font=('Arial', 72, 'bold'), 
                                           fg='white', bg='#3498db')
        self.player1_score_label.pack(pady=20)
        
        self.player1_serve_label = tk.Label(p1_frame, text="", 
                                           font=('Arial', 16, 'bold'), 
                                           fg='#f1c40f', bg='#3498db')
        self.player1_serve_label.pack(pady=(0, 10))
        
        # VS label
        vs_label = tk.Label(score_frame, text="VS", 
                           font=('Arial', 24, 'bold'), 
                           fg='#ecf0f1', bg='#2c3e50')
        vs_label.pack(side=tk.LEFT, padx=20)
        
        # Player 2 score section
        p2_frame = tk.Frame(score_frame, bg='#e74c3c', relief=tk.RAISED, bd=3)
        p2_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.player2_label = tk.Label(p2_frame, text=self.player2_name, 
                                     font=('Arial', 20, 'bold'), 
                                     fg='white', bg='#e74c3c')
        self.player2_label.pack(pady=10)
        
        self.player2_score_label = tk.Label(p2_frame, text="0", 
                                           font=('Arial', 72, 'bold'), 
                                           fg='white', bg='#e74c3c')
        self.player2_score_label.pack(pady=20)
        
        self.player2_serve_label = tk.Label(p2_frame, text="", 
                                           font=('Arial', 16, 'bold'), 
                                           fg='#f1c40f', bg='#e74c3c')
        self.player2_serve_label.pack(pady=(0, 10))
        
        # Game controls
        controls_frame = tk.Frame(self.game_frame, bg='#2c3e50')
        controls_frame.pack(pady=30)
        
        reset_btn = tk.Button(controls_frame, text="RESET GAME", 
                             font=('Arial', 14, 'bold'), 
                             bg='#f39c12', fg='white',
                             command=self.reset_game, 
                             padx=20, pady=10)
        reset_btn.pack(side=tk.LEFT, padx=10)
        
        new_game_btn = tk.Button(controls_frame, text="NEW GAME", 
                                font=('Arial', 14, 'bold'), 
                                bg='#9b59b6', fg='white',
                                command=self.new_game, 
                                padx=20, pady=10)
        new_game_btn.pack(side=tk.LEFT, padx=10)
        
        exit_btn = tk.Button(controls_frame, text="EXIT", 
                            font=('Arial', 14, 'bold'), 
                            bg='#e74c3c', fg='white',
                            command=self.exit_app, 
                            padx=20, pady=10)
        exit_btn.pack(side=tk.LEFT, padx=10)
        
        # Test mode instructions during game
        test_instructions = tk.Label(self.game_frame, 
                                    text="TEST MODE: Press 'A' for Player 1 • Press 'L' for Player 2 • Or use buttons below", 
                                    font=('Arial', 12), 
                                    fg='#f39c12', bg='#2c3e50')
        test_instructions.pack(pady=10)
        
        # Test buttons during game
        game_test_frame = tk.Frame(self.game_frame, bg='#2c3e50')
        game_test_frame.pack(pady=10)
        
        self.game_test_p1_btn = tk.Button(game_test_frame, text="Player 1 Score (A)", 
                                         font=('Arial', 12), bg='#3498db', fg='white',
                                         command=self.player1_scored_test, padx=20, pady=10)
        self.game_test_p1_btn.pack(side=tk.LEFT, padx=10)
        
        self.game_test_p2_btn = tk.Button(game_test_frame, text="Player 2 Score (L)", 
                                         font=('Arial', 12), bg='#e74c3c', fg='white',
                                         command=self.player2_scored_test, padx=20, pady=10)
        self.game_test_p2_btn.pack(side=tk.LEFT, padx=10)
        
    def setup_keyboard_bindings(self):
        """Setup keyboard bindings for testing"""
        self.root.bind('<KeyPress-a>', lambda e: self.player1_scored_test())
        self.root.bind('<KeyPress-A>', lambda e: self.player1_scored_test())
        self.root.bind('<KeyPress-l>', lambda e: self.player2_scored_test())
        self.root.bind('<KeyPress-L>', lambda e: self.player2_scored_test())
        
        # Make sure the window can receive key events
        self.root.focus_set()
        
    def start_game(self):
        """Start the game with selected players"""
        self.player1_name = self.player1_entry.get().strip() or "Player 1"
        self.player2_name = self.player2_entry.get().strip() or "Player 2"
        
        # Update labels
        self.player1_label.config(text=self.player1_name)
        self.player2_label.config(text=self.player2_name)
        
        # Update test button labels
        self.game_test_p1_btn.config(text=f"{self.player1_name} Score (A)")
        self.game_test_p2_btn.config(text=f"{self.player2_name} Score (L)")
        
        # Switch to game view
        self.setup_frame.pack_forget()
        self.game_frame.pack(fill=tk.BOTH, expand=True)
        
        self.game_started = True
        self.serving_player = 1  # Player 1 serves first
        self.update_serve_display()
        
        # Play start sound
        self.play_sound('start')
        
        # Ensure window can still receive key events
        self.root.focus_set()
        
    def player1_scored_test(self):
        """Handle Player 1 scoring (test version)"""
        if not self.game_started or self.game_over:
            return
            
        self.player1_score += 1
        self.points_to_serve += 1
        self.update_score_display()
        self.check_serve_change()
        self.check_game_over()
        self.play_sound('score')
        print(f"Player 1 ({self.player1_name}) scored! Score: {self.player1_score}")
        
    def player2_scored_test(self):
        """Handle Player 2 scoring (test version)"""
        if not self.game_started or self.game_over:
            return
            
        self.player2_score += 1
        self.points_to_serve += 1
        self.update_score_display()
        self.check_serve_change()
        self.check_game_over()
        self.play_sound('score')
        print(f"Player 2 ({self.player2_name}) scored! Score: {self.player2_score}")
        
    def update_score_display(self):
        """Update the score display"""
        self.player1_score_label.config(text=str(self.player1_score))
        self.player2_score_label.config(text=str(self.player2_score))
        
    def check_serve_change(self):
        """Check if serve should change (every 2 points in standard ping pong)"""
        if self.points_to_serve >= 2:
            self.serving_player = 2 if self.serving_player == 1 else 1
            self.points_to_serve = 0
            self.update_serve_display()
            print(f"Serve changed to {self.player1_name if self.serving_player == 1 else self.player2_name}")
            
    def update_serve_display(self):
        """Update the serving indicator"""
        if self.serving_player == 1:
            self.player1_serve_label.config(text="🏓 SERVING")
            self.player2_serve_label.config(text="")
        else:
            self.player1_serve_label.config(text="")
            self.player2_serve_label.config(text="🏓 SERVING")
            
    def check_game_over(self):
        """Check if game is over (first to 11, win by 2)"""
        if (self.player1_score >= 11 or self.player2_score >= 11):
            if abs(self.player1_score - self.player2_score) >= 2:
                self.game_over = True
                winner = self.player1_name if self.player1_score > self.player2_score else self.player2_name
                self.play_sound('win')
                print(f"Game Over! {winner} wins!")
                messagebox.showinfo("Game Over!", f"🏆 {winner} Wins!\n\nFinal Score:\n{self.player1_name}: {self.player1_score}\n{self.player2_name}: {self.player2_score}")
                
    def play_sound(self, sound_type):
        """Play sound effects"""
        if not self.sound_enabled:
            return
            
        try:
            if sound_type == 'score':
                # Create a simple beep sound
                self.create_beep_sound(440, 0.1)  # 440Hz for 0.1 seconds
            elif sound_type == 'start':
                # Create a start game sound
                self.create_beep_sound(523, 0.2)  # C note
            elif sound_type == 'win':
                # Create a victory sound
                for freq in [523, 659, 784]:  # C-E-G chord
                    self.create_beep_sound(freq, 0.3)
                    time.sleep(0.1)
        except Exception as e:
            print(f"Sound error: {e}")
            
    def create_beep_sound(self, frequency, duration):
        """Create and play a beep sound"""
        try:
            # Generate a simple sine wave
            sample_rate = 22050
            frames = int(duration * sample_rate)
            arr = []
            for i in range(frames):
                wave = 4096 * (i % (sample_rate // frequency) < (sample_rate // frequency) // 2) - 2048
                arr.append([wave, wave])
            
            sound = pygame.sndarray.make_sound(pygame.array.array('h', arr))
            sound.play()
            time.sleep(duration)
        except Exception as e:
            print(f"Beep sound error: {e}")
            
    def reset_game(self):
        """Reset the current game scores"""
        self.player1_score = 0
        self.player2_score = 0
        self.serving_player = 1
        self.points_to_serve = 0
        self.game_over = False
        self.update_score_display()
        self.update_serve_display()
        self.play_sound('start')
        print("Game reset!")
        
    def new_game(self):
        """Start a completely new game with player selection"""
        self.game_started = False
        self.game_over = False
        self.player1_score = 0
        self.player2_score = 0
        self.serving_player = 1
        self.points_to_serve = 0
        
        # Switch back to setup view
        self.game_frame.pack_forget()
        self.setup_frame.pack(fill=tk.BOTH, expand=True)
        self.root.focus_set()
        print("Starting new game...")
        
    def exit_app(self):
        """Exit the application"""
        self.cleanup()
        self.root.quit()
        
    def cleanup(self):
        """Clean up pygame"""
        try:
            if self.sound_enabled:
                pygame.mixer.quit()
        except Exception as e:
            print(f"Cleanup error: {e}")
            
    def run(self):
        """Run the application"""
        try:
            # Bind F11 to toggle fullscreen for testing
            self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen')))
            self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
            
            # Handle window close
            self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
            
            print("=== PING PONG SCORER TEST MODE ===")
            print("Controls:")
            print("  - Press 'A' key for Player 1 score")
            print("  - Press 'L' key for Player 2 score")
            print("  - Or click the test buttons")
            print("  - F11 to toggle fullscreen")
            print("  - Escape to exit fullscreen")
            print("=====================================")
            
            # Start the GUI
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Application interrupted")
        finally:
            self.cleanup()

if __name__ == "__main__":
    try:
        app = PingPongScorerTest()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")