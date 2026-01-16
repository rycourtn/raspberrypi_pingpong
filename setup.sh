#!/bin/bash
# Setup script for Ping Pong Scorer on Raspberry Pi

echo "🏓 Setting up Ping Pong Scorer..."

# Update system
echo "Updating system packages..."
sudo apt update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3-pygame python3-flask alsa-utils

# Make the main script executable
chmod +x ping_pong_scorer.py

# Create desktop shortcut
echo "Creating desktop shortcut..."
mkdir -p ~/Desktop
cat > ~/Desktop/PingPongScorer.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Ping Pong Scorer
Comment=Ping pong scoring system
Exec=python3 $(pwd)/ping_pong_scorer.py
Icon=applications-games
Terminal=false
Categories=Game;
EOF

chmod +x ~/Desktop/PingPongScorer.desktop

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the scorer:"
echo "  python3 ping_pong_scorer.py"
echo ""
echo "Or double-click 'Ping Pong Scorer' on your desktop"
echo ""