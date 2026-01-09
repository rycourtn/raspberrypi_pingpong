# 🏓 Ping Pong Scorer for Raspberry Pi

A GPIO-based ping pong scoring system with GUI display perfect for VNC Viewer.

## Features

- **GPIO Button Control**: Buttons on GPIO pins 15 and 18 for scoring
- **Player Selection**: Choose player names before starting the game
- **Serving Tracker**: Automatically tracks who is serving (changes every 2 points)
- **Sound Effects**: Audio feedback through speakers for button presses
- **Fullscreen GUI**: Optimized for VNC Viewer display
- **Game Rules**: First to 11 points, must win by 2

## Hardware Setup

### Required Components
- Raspberry Pi (any model with GPIO)
- 2x Push buttons
- 2x 10kΩ resistors (for pull-up if needed)
- Breadboard and jumper wires
- Speaker or audio output device

### Wiring
```
Button 1 (Player 1): GPIO 15 → Button → Ground
Button 2 (Player 2): GPIO 18 → Button → Ground
```

The code uses internal pull-up resistors, so external pull-ups are optional.

## Software Setup

### Quick Setup
```bash
# Clone or download the files
# Run the setup script
chmod +x setup.sh
./setup.sh
```

### Manual Setup
```bash
# Install dependencies
sudo apt update
sudo apt install -y python3-pygame alsa-utils
pip3 install RPi.GPIO pygame

# Run the application
python3 ping_pong_scorer.py
```

## Usage

1. **Start the Application**: Run `python3 ping_pong_scorer.py`
2. **Enter Player Names**: Type in the names for both players
3. **Start Game**: Click "START GAME" button
4. **Score Points**: Press the GPIO buttons to score for each player
5. **Game Controls**: Use on-screen buttons to reset or start new games

### Keyboard Shortcuts
- `Escape`: Exit fullscreen mode
- `F11`: Enter fullscreen mode

## Game Rules

- First player to reach 11 points wins
- Must win by at least 2 points
- Serve changes every 2 points
- Player 1 serves first

## Sound Effects

The system plays different sounds for:
- **Score**: Short beep when a point is scored
- **Game Start**: Musical note when game begins
- **Victory**: Chord progression when game ends

## VNC Viewer Optimization

The GUI is designed for VNC Viewer with:
- Fullscreen mode by default
- Large, clear fonts and buttons
- High contrast colors
- Touch-friendly interface

## Troubleshooting

### GPIO Permission Issues
```bash
sudo usermod -a -G gpio $USER
# Log out and back in
```

### Audio Issues
```bash
# Test audio
speaker-test -t sine -f 1000 -l 1

# Check audio devices
aplay -l
```

### Python Module Issues
```bash
# Reinstall packages
pip3 install --upgrade RPi.GPIO pygame
```

## Customization

### Changing GPIO Pins
Edit the GPIO pin numbers in `ping_pong_scorer.py`:
```python
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Change 15 to your pin
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Change 18 to your pin
```

### Modifying Game Rules
- Change winning score: Modify the `check_game_over()` method
- Change serve frequency: Modify the serve change logic in `check_serve_change()`
- Customize sounds: Edit the `play_sound()` method

## Files

- `ping_pong_scorer.py`: Main application
- `requirements.txt`: Python dependencies
- `setup.sh`: Automated setup script
- `README.md`: This documentation

## License

Open source - feel free to modify and improve!