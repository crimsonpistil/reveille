\# Reveille



A Discord bot that generates and posts a military-style daily intelligence brief every morning at 0800 Eastern, powered by Claude AI. Pulls from a curated list of RSS feeds covering U.S. military news, geopolitical developments, OSINT sources, cyber threats, and veteran affairs.



Named after the bugle call that starts the military day.



---



\## Features



\- Automated daily brief posted every morning at 0800 Eastern

\- AI-generated intel-style formatting via the Anthropic Claude API

\- 25 RSS sources across mil/DoD, geopolitical, OSINT, cyber, and veteran affairs

\- Deduplication system — no repeat stories day to day

\- Auto-creates a discussion thread on each brief (auto-archives after 24 hours)

\- `/brief` — authorized users can trigger a brief on demand

\- `/briefstatus` — check how long until the next scheduled brief



---



\## Brief Format



```

═══════════════════════════════════════

REVEILLE -- DAILY BRIEF

13 MARCH 2026 | 0800 EASTERN

═══════════════════════════════════════



EXECUTIVE SUMMARY

\[2-3 sentence overview of the day's most significant developments]



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

U.S. MILITARY \& DOD

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• ...



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GEOPOLITICS \& THINK TANKS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• ...



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INTELLIGENCE \& OSINT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• ...



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CYBER \& VETERAN AFFAIRS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• ...



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANALYST NOTE

\[Closing observation or item to watch]

═══════════════════════════════════════

```



---



\## Tech Stack



\- \*\*Python 3.11\*\*

\- \*\*discord.py 2.x\*\* — slash commands and task loops

\- \*\*Anthropic Claude API\*\* — AI-generated brief writing and summarization

\- \*\*feedparser\*\* — RSS feed parsing

\- \*\*python-dotenv\*\* — secure credential handling

\- \*\*Railway\*\* — cloud hosting for 24/7 uptime

\- \*\*GitHub\*\* — version control and auto-deploy pipeline



---



\## RSS Sources



| Category | Sources |

|---|---|

| U.S. Military / DoD | Defense One, Military Times, DoD News, Stars and Stripes, Defense News, Task \& Purpose, Breaking Defense, USNI News, Naval News, Aviation Week Defense, Space Force News |

| Geopolitics \& Think Tanks | War on the Rocks, Foreign Policy, ISW, RAND Corporation, Small Wars Journal |

| Intelligence \& OSINT | Recorded Future (The Record), Recorded Future (Insikt Group), Bellingcat, The War Zone, Oryx, CISA Alerts, ODNI News |

| Cyber \& Veteran Affairs | Krebs on Security, VA News |



---



\## How Deduplication Works



Every article URL that gets included in a brief is saved to `seen.json` on the Railway persistent volume. On each run the bot checks incoming articles against this list and skips anything already reported. Entries expire after 7 days so recurring topics can resurface after a week.



---



\## Setup



\### Prerequisites

\- Python 3.10+

\- A Discord bot token (\[Discord Developer Portal](https://discord.com/developers/applications))

\- An Anthropic API key (\[console.anthropic.com](https://console.anthropic.com))



\### 1. Clone the repo

```bash

git clone https://github.com/crimsonpistil/reveille.git

cd reveille

```



\### 2. Install dependencies

```bash

pip install -r requirements.txt

```



\### 3. Configure environment

Create a `.env` file in the project root:

```

DISCORD\_TOKEN=your-discord-bot-token

ANTHROPIC\_API\_KEY=your-anthropic-api-key

```



\### 4. Configure the bot

Open `bot.py` and update:

```python

BRIEF\_CHANNEL\_ID = 000000000000       # Right-click channel -> Copy Channel ID

BRIEF\_HOUR\_UTC = 13                   # 0800 Eastern Standard = 1300 UTC

AUTHORIZED\_USER\_IDS = {               # Discord user IDs allowed to run /brief

&nbsp;   000000000000000000,

}

```



\### 5. Discord Developer Portal setup

\- Enable \*\*Server Members Intent\*\* and \*\*Message Content Intent\*\*

\- Invite with scopes: `bot`, `applications.commands`

\- Bot permissions: `Send Messages`, `View Channels`, `Embed Links`, `Create Public Threads`, `Send Messages in Threads`, `Read Message History`



\### 6. Channel permissions

Set `#daily-brief` so only the bot can post:

\- @everyone: Send Messages -> off, Send Messages in Threads -> on, View Channel -> on

\- Reveille bot role: Send Messages -> on



\### 7. Run locally

```bash

python bot.py

```



---



\## Cloud Deployment (Railway)



1\. Push repo to GitHub

2\. Connect to \[Railway](https://railway.app) via \*\*Deploy from GitHub\*\*

3\. Add environment variables:

&nbsp;  - `DISCORD\_TOKEN`

&nbsp;  - `ANTHROPIC\_API\_KEY`

4\. Add a Volume with mount path `/data` for deduplication persistence

5\. Railway auto-deploys on every `git push`



---



\## Adding RSS Feeds



Open `bot.py` and add a new line to the `RSS\_FEEDS` list:

```python

("Source Name", "https://the-rss-feed-url.com/feed"),

```



---



\## Project Structure



```

reveille/

├── bot.py            # Main bot logic

├── requirements.txt  # Dependencies

├── .env              # Secret credentials (not committed)

├── .gitignore        # Excludes .env and cache files

└── README.md         # This file

```



---



\## Security Notes



\- `.env` is excluded from version control via `.gitignore`

\- All credentials loaded from environment variables, never hardcoded

\- `/brief` command restricted to authorized user IDs only

\- No member data collected or stored — only article URLs



---



\## Cost



Reveille uses the Anthropic Claude API on a pay-as-you-go basis. A single daily brief costs approximately $0.01-0.03 depending on headline volume — roughly $0.30-$1.00/month.



---



\## License



MIT — free to use, modify, and deploy.

