# Reveille

A Discord bot that generates and posts a military-style daily intelligence brief every morning at 0800 Eastern, powered by Claude AI. Pulls from a curated list of RSS feeds covering U.S. military news, geopolitical developments, OSINT sources, cyber threats, and veteran affairs.

Named after the bugle call that starts the military day, aka Crimson's former life.

---

## Features

- Automated daily brief posted every morning at 0800 Eastern
- AI-generated intel-style formatting via the Anthropic Claude API
- 25 RSS sources across mil/DoD, geopolitical, OSINT, cyber, and veteran affairs
- Deduplication system — no repeat stories day to day, entries expire after 7 days
- Auto-creates a discussion thread on each brief
- Threads auto-archive after 2 days and are permanently deleted after 2 weeks
- Multi-server support — each server configures its own channel via `/setchannel`
- `/brief` restricted to authorized user IDs to protect API costs

---

## Commands

| Command | Access | Description |
|---|---|---|
| `/setchannel` | Manage Server | Set the channel for daily briefs in this server |
| `/brief` | Authorized users only | Generate and post today's brief on demand |
| `/briefstatus` | Everyone | Check when the next brief is scheduled |
| `/clearseen` | Authorized users only | Clear the seen articles cache for a fresh brief |

---

## Brief Format

```
DAILY BRIEF // DATE | TIME 

- EXECUTIVE SUMMARY: Two sentence overview of the day's most significant developments
- U.S. MILITARY & DOD
- GEOPOLITICS & THINK TANKS
- INTELLIGENCE & OSINT
- VETERAN AFFAIRS
- ANALYST NOTE: Closing observation or item to watch
```

---

## Tech Stack

- **Python 3.11**
- **discord.py 2.x** — slash commands and task loops
- **Anthropic Claude API** — AI-generated brief writing and summarization
- **feedparser** — RSS feed parsing
- **python-dotenv** — secure credential handling
- **Railway** — cloud hosting for 24/7 uptime
- **GitHub** — version control and auto-deploy pipeline

---

## RSS Sources

| Category | Sources |
|---|---|
| U.S. Military / DoD | Defense One, Military Times, DoD News, Stars and Stripes, Defense News, Task & Purpose, Breaking Defense, USNI News, Naval News, Aviation Week Defense, Space Force News |
| Geopolitics & Think Tanks | War on the Rocks, Foreign Policy, ISW, RAND Corporation, Small Wars Journal |
| Intelligence & OSINT | Recorded Future (The Record), Recorded Future (Insikt Group), Bellingcat, The War Zone, Oryx, CISA Alerts, ODNI News,  Krebs on Security |
| Veteran Affairs | VA News |

---

## How Deduplication Works

Every article URL included in a brief is saved to `seen.json` on the Railway persistent volume. On each run the bot checks incoming articles against this list and skips anything already reported. Entries expire after 7 days so recurring topics can resurface after a week. Use `/clearseen` to manually reset the cache.

---

## Multi-Server Support

Reveille can run in multiple Discord servers simultaneously from a single deployment. Each server configures its own brief channel using `/setchannel`. Channel mappings are stored in `channels.json` on the persistent volume. If no channel has been configured for a server, Reveille falls back to the default `BRIEF_CHANNEL_ID` in the code.

---

## Setup

### Prerequisites
- Python 3.10+
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

### 1. Clone the repo
```bash
git clone https://github.com/crimsonpistil/reveille.git
cd reveille
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Create a `.env` file in the project root:
```
DISCORD_TOKEN=your-discord-bot-token
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### 4. Configure the bot
Open `bot.py` and update:
```python
BRIEF_CHANNEL_ID = 000000000000       # Fallback channel ID
AUTHORIZED_USER_IDS = {
    000000000000000000,                # Your Discord user ID
}
```

### 5. Discord Developer Portal setup
- Enable **Server Members Intent** and **Message Content Intent**
- Invite with scopes: `bot`, `applications.commands`
- Bot permissions: `Send Messages`, `View Channels`, `Embed Links`, `Create Public Threads`, `Send Messages in Threads`, `Read Message History`

### 6. Channel permissions
Set your brief channel so only the bot can post:
- @everyone: Send Messages -> off, Send Messages in Threads -> on, View Channel -> on
- Reveille bot role: Send Messages -> on, Create Public Threads -> on

### 7. Set the brief channel in Discord
```
/setchannel #your-channel
```

### 8. Run locally
```bash
python bot.py
```

---

## Cloud Deployment (Railway)

1. Push repo to GitHub
2. Connect to [Railway](https://railway.app) via **Deploy from GitHub**
3. Add environment variables:
   - `DISCORD_TOKEN`
   - `ANTHROPIC_API_KEY`
4. Add a Volume with mount path `/data` for deduplication and channel config persistence
5. Railway auto-deploys on every `git push`

---

## Adding RSS Feeds

Open `bot.py` and add a new line to the `RSS_FEEDS` list:
```python
("Source Name", "https://the-rss-feed-url.com/feed"),
```

---

## Project Structure

```
reveille/
├── bot.py            # Main bot logic
├── requirements.txt  # Dependencies
├── .env              # Secret credentials (not committed)
├── .gitignore        # Excludes .env and cache files
└── README.md         # You are here lol
```

---

## Security Notes

- `.env` is excluded from version control via `.gitignore`
- All credentials loaded from environment variables, never hardcoded
- `/brief` and `/clearseen` restricted to authorized user IDs to protect API costs
- No member data collected or stored

---

## Cost

Reveille uses the Anthropic Claude API on a pay-as-you-go basis. A single daily brief costs approximately $0.01-0.03 depending on headline volume — roughly $0.30-$1.00/month.

---

## License

MIT — free to use, modify, and deploy.
