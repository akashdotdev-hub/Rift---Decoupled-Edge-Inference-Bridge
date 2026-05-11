#!/bin/bash
# ---------------------------------------------------------
# Rift: Hybrid Cloud Inference Bridge
# Script: daemonize.sh
# Purpose: Configures the bot to run 24/7 in the background
# ---------------------------------------------------------

echo "⚙️  Initializing Rift Gateway Service..."

# 1. Define Environment Variables
APP_USER="ec2-user"
PROJECT_DIR="/home/ec2-user/rift-inference-bridge"
SERVICE_FILE="/etc/systemd/system/rift-gateway.service"

# 2. Generate the systemd configuration file
# We use sudo tee to safely write to the protected /etc directory
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Rift AI Discord Gateway
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $PROJECT_DIR/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 3. Apply changes to the Linux kernel
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "🚀 Enabling and starting the Rift Gateway..."
sudo systemctl enable rift-gateway
sudo systemctl start rift-gateway

echo ""
echo "✅ SUCCESS: Rift Gateway is now locked into the background!"
echo "---------------------------------------------------------"
echo "📊 USEFUL COMMANDS:"
echo "View Live Logs:   journalctl -u rift-gateway -f"
echo "Stop the Bot:     sudo systemctl stop rift-gateway"
echo "Restart the Bot:  sudo systemctl restart rift-gateway"
echo "---------------------------------------------------------"
