#!/usr/bin/env python3
"""
Ping Pong Scoring System for Raspberry Pi
- GPIO buttons on pins 15 and 18 for scoring
- GUI display for VNC Viewer
- Player selection and serving tracking
- Sound effects for button presses
"""

import tkinter as tk
from tkinter import ttk, messagebox
import RPi.GPIO as GPIO
import pygame
import threading
import time
import os

class PingPongScorer:
    def __init__(self):
        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Player 1 button
        GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Player 2 button
        
        # Initialize pygame for sound
        pygame.mixer.init()
        
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
        self.root.title("Ping Pong Scorer")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Make window fullscreen for better VNC experience
        self.root.attributes('-fullscreen', True)
        
        self.setup_gui()
        self.setup_gpio_callbacks()
        
    def setup_gui(self):
        """Setup the GUI interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="🏓 PING PONG SCORER 🏓", 
                              font=('Arial', 24, 'bold'), 
                              fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=(0, 30))
        
        # Player setup frame (shown before game starts)
        self.setup_frame = tk.Frame(main_frame, bg='#2c3e50')
        self.setup_frame.pack(fill=tk.BOTH, expand=True)
        
        # Player name inputs
        tk.Label(self.setup_frame, text="Enter Player Names:", 
                font=('Arial', 18, 'bold'), fg='#ecf0f1', bg='#2c3e50').pack(pady=20)
        
        input_frame = tk.Frame(self.setup_frame, bg='#2c3e50')
        input_frame.pack(pady=20)
        
        tk.Label(input_frame, text="Player 1 (GPIO 15):", 
                font=('Arial', 14), fg='#ecf0f1', bg='#2c3e50').grid(row=0, column=0, padx=10, pady=10)
        self.player1_entry = tk.Entry(input_frame, font=('Arial', 14), width=20)
        self.player1_entry.grid(row=0, column=1, padx=10, pady=10)
        self.player1_entry.insert(0, self.player1_name)
        
        tk.Label(input_frame, text="Player 2 (GPIO 18):", 
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
        
        # Instructions
        instructions = tk.Label(self.game_frame, 
                               text="Press GPIO 15 button for Player 1 • Press GPIO 18 button for Player 2", 
                               font=('Arial', 12), 
                               fg='#bdc3c7', bg='#2c3e50')
        instructions.pack(pady=20)
        
    def setup_gpio_callbacks(self):
        """Setup GPIO button callbacks"""
        GPIO.add_event_detect(15, GPIO.FALLING, callback=self.player1_scored, bouncetime=300)
        GPIO.add_event_detect(18, GPIO.FALLING, callback=self.player2_scored, bouncetime=300)
        
    def start_game(self):
        """Start the game with selected players"""
        self.player1_name = self.player1_entry.get().strip() or "Player 1"
        self.player2_name = self.player2_entry.get().strip() or "Player 2"
        
        # Update labels
        self.player1_label.config(text=self.player1_name)
        self.player2_label.config(text=self.player2_name)
        
        # Switch to game view
        self.setup_frame.pack_forget()
        self.game_frame.pack(fill=tk.BOTH, expand=True)
        
        self.game_started = True
        self.serving_player = 1  # Player 1 serves first
        self.update_serve_display()
        
        # Play start sound
        self.play_sound('start')
        
    def player1_scored(self, channel):
        """Handle Player 1 scoring"""
        if not self.game_started or self.game_over:
            return
            
        self.player1_score += 1
        self.points_to_serve += 1
        self.update_score_display()
        self.check_serve_change()
        self.check_game_over()
        self.play_sound('score')
        
    def player2_scored(self, channel):
        """Handle Player 2 scoring"""
        if not self.game_started or self.game_over:
            return
            
        self.player2_score += 1
        self.points_to_serve += 1
        self.update_score_display()
        self.check_serve_change()
        self.check_game_over()
        self.play_sound('score')
        
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
                messagebox.showinfo("Game Over!", f"🏆 {winner} Wins!\n\nFinal Score:\n{self.player1_name}: {self.player1_score}\n{self.player2_name}: {self.player2_score}")
                
    def play_sound(self, sound_type):
        """Play sound effects"""
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
        
    def exit_app(self):
        """Exit the application"""
        self.cleanup()
        self.root.quit()
        
    def cleanup(self):
        """Clean up GPIO and pygame"""
        try:
            GPIO.cleanup()
            pygame.mixer.quit()
        except Exception as e:
            print(f"Cleanup error: {e}")
            
    def run(self):
        """Run the application"""
        try:
            # Bind escape key to exit fullscreen
            self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
            self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', True))
            
            # Handle window close
            self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
            
            # Start the GUI
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Application interrupted")
        finally:
            self.cleanup()

if __name__ == "__main__":
    try:
        app = PingPongScorer()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        GPIO.cleanup()