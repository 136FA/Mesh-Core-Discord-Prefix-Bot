# MeshCore Prefix Bot

A Discord bot for tracking MeshCore repeater public key prefixes across a mesh network. Maintains a 16×16 hex grid showing which 2-character prefixes are in use, who owns each node, and allows easy management via slash commands.

## Setup

### 1. Clone and install

```bash
git clone (https://github.com/136FA/Mesh-Core-Discord-Prefix-Bot)
cd Mesh-Core-Discord-Prefix-Bot
python3 -m venv botenv
source botenv/bin/activate
pip install -r requirements.txt
```

### 2. Create a Discord bot

1. Go to https://discord.com/developers/applications
2. **New Application** → give it a name
3. **Bot** → **Add Bot** → copy the token
4. Paste your token into `bot.py` replacing `YOUR_BOT_TOKEN_HERE`
5. **OAuth2 → URL Generator** → check `bot` + `applications.commands`
6. Bot Permissions: **Send Messages** + **Use Slash Commands**
7. Open the generated URL to invite the bot to your server

### 3. Run

```bash
python3 bot.py
```

On first run, `prefixes.json` is created automatically seeded with the current node list.

---

## Running headlessly with systemd

```bash
sudo nano /etc/systemd/system/meshbot.service
```

```ini
[Unit]
Description=MeshCore Prefix Bot
After=network.target

[Service]
User=YOUR_LINUX_USERNAME
WorkingDirectory=/home/YOUR_LINUX_USERNAME/meshcore-prefix-bot
ExecStart=/home/YOUR_LINUX_USERNAME/meshcore-prefix-bot/botenv/bin/python3 bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable meshbot
sudo systemctl start meshbot
```

Useful commands:
```bash
sudo systemctl status meshbot       # check status
sudo systemctl restart meshbot      # restart after updating bot.py
sudo journalctl -u meshbot -f       # live logs
```

---

## Commands

| Command | Description |
|---|---|
| `/prefix-show` | Post the ANSI color grid |
| `/prefix-add C3 My Repeater @jake` | Mark a prefix as used with name and optional owner |
| `/prefix-remove C3` | Free a prefix |
| `/prefix-update C3 name:New Name owner:@jake` | Update name and/or owner |
| `/prefix-clear-owner C3` | Remove the owner from a prefix |
| `/prefix-list` | List all used prefixes, names, and owners |
