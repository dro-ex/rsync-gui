#!/usr/bin/env bash
set -euo pipefail

# install system deps
apt-get update
apt-get install -y python3 python3-venv python3-dev build-essential

# set up venv
python3 -m venv venv
. venv/bin/activate

# install Python deps
pip install --upgrade pip
pip install -r requirements.txt

# create systemd service
cat > /etc/systemd/system/rsync-gui.service <<EOF
[Unit]
Description=Rsync GUI Web Service
After=network.target

[Service]
User=root
WorkingDirectory=/opt/rsync-gui
ExecStart=/opt/rsync-gui/venv/bin/python app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable rsync-gui
systemctl start rsync-gui

echo "Rsync GUI installed and running."
