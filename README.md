# Discord Staff Activity & Attendance Bot

A complete bot to manage and track your staff team's activity time on Discord. Inspired by professional attendance systems, it offers an interactive dashboard, role-based time goals, AFK detection, and a ranking system — all open-source.

## Features

* **Interactive Activity Panel**: Staff members can start or stop their activity with a click, check their stats, and access the activity ranking.
* **Role-Based Time Goals**: Set custom activity quotas for each role to encourage engagement.
* **AFK Detection**: The bot automatically checks if a member went AFK and stops their timer if they don’t respond, ensuring accurate tracking.
* **Automatic Reminders**: Sends friendly DMs to remind team members who haven’t met their weekly goals yet (with cooldowns to prevent spam).
* **Detailed Stats**: Members can see their total contribution time, progress toward goals, and last activity sessions.
* **Activity Ranking**: A “Top Staffs” button displays the most active team members, promoting healthy competition.
* **Staff Commands**: Modern slash commands for admins to configure the panel and check member activity.
* **Administrative Logs**: Records important events, such as AFK stops and goal reminders, in a dedicated log channel.

## Setup Guide

Follow these steps to get your activity bot running on your Discord server.

### 1. Requirements

Before starting, make sure you have:
* Python 3.8 or newer.
* A Discord Bot Account with your **Token**.
* The **Server Members** and **Message Content** intents enabled in the [Discord Developer Portal](https://discord.com/developers/applications).

### 2. Installation & Configuration

Setup is simple — just edit the variables at the top of the main Python file.

**Step 1: Get the Code**
Clone or download the bot’s files to your computer or server.

**Step 2: Install Dependencies**
Install all required Python libraries (assuming you have a `requirements.txt` file):
```bash
pip install discord.py
# (If you have a requirements.txt file, use)
pip install -r requirements.txt
```

**Step 3: Configure the Bot**
Open your main Python file (e.g., bot.py). At the top, you’ll find configuration variables. Replace the example values with the correct IDs from your server.

**How to Get Discord IDs:**
1. Go to *User Settings > Advanced*.
2. Enable *Developer Mode*.
3. Now you can right-click any user, role, channel, or category to **Copy ID**.

```python
# Edit these values at the top of your file

# Channel and Role IDs
LOG_CHANNEL_ID = 1428471793496358942             # Channel ID for logs
AFK_LOG_PING_ROLE_ID = 1342569119869829123       # Role ID to mention in AFK logs

# Role-Based Activity Goals
# Structure: ROLE_ID: {"name": "Role Name", "seconds": GOAL_IN_SECONDS}
CARGOS_PONTO = {
    1342569124554866801: {"name": "Helper", "seconds": 30 * 60},      # 30-minute goal
    1342569120981454868: {"name": "Admin", "seconds": 90 * 60},       # 90-minute goal
    1342569121736294505: {"name": "Moderator", "seconds": 60 * 60},   # 60-minute goal
    1401918325235388497: {"name": "Intern", "seconds": 25 * 60}       # 25-minute goal
}

# (Optional) You can also customize image URLs and emojis
LOGO_URL = "https://..."
IMAGE_URL = "https://..."
EMOJI_START = "<a:relogio:1428460234137141418>"
# ... etc
```

**Step 4: Run the Bot**
You’re all set! Start the bot using this command (make sure to add your token in the startup code if you haven’t yet):

```bash
python bot.py
```

## Commands

Once the bot is online:

### `/activitypanel`
Use this command in the channel where you want the “Activity Center” panel to appear. Admin-only command.

### `/checkactivity [member]`
View a detailed summary of a member’s total activity, goal progress, and recent sessions. Admin-only command.

---

## License
This project is free for personal and community use. Resale or commercial use is not allowed without prior authorization.
