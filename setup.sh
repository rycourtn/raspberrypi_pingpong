#!/bin/bash
# Setup script for Ping Pong Scorer

echo "Setting up Ping Pong Scorer..."

# Update system
sudo apt update

# Install Python dependencies
echo "Installing Python packages..."
pip3 install -r requirements.txt

# Install system audio dependencies for pygame
echo "Installing system audio dependencies..."
sudo apt install -y python3-pygame alsa-utils

# Make the main script executable
chmod +x ping_pong_scorer.py

# Create desktop shortcut
echo "Creating desktop shortcut..."
cat > ~/Desktop/PingPongScorer.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Ping Pong Scorer
Comment=GPIO-based ping pong scoring system
Exec=python3 $(pwd)/ping_pong_scorer.py
Icon=applications-games
Terminal=false
Categories=Game;
EOF

chmod +x ~/Desktop/PingPongScorer.desktop

echo "Setup complete!"
echo "You can now run the scorer with: python3 ping_pong_scorer.py"
echo "Or use the desktop shortcut: Ping Pong Scorer"