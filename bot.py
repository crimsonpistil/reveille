import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import feedparser
import anthropic

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ── Configuration ──────────────────────────────────────────────────────────────
BRIEF_CHANNEL_ID = 1482095132290318346  # 📜・daily-brief
BRIEF_HOUR_UTC = 13      # 0800 Eastern Standard = 1300 UTC
BRIEF_MINUTE_UTC = 0

# ── RSS Feed Sources ───────────────────────────────────────────────────────────
RSS_FEEDS = [
    # US Military / DoD
    ("Defense One", "https://www.defenseone.com/rss/all/"),
    ("Military Times", "https://www.militarytimes.com/arc/outboundfeeds/rss/"),
    ("DoD News", "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10"),
    ("Stars and Stripes", "https://www.stripes.com/arc/outboundfeeds/rss/"),
    ("Defense News", "https://www.defensenews.com/arc/outboundfeeds/rss/"),
    ("Task & Purpose", "https://taskandpurpose.com/feed/"),
    # Geopolitical
    ("Reuters World", "https://feeds.reuters.com/reuters/worldNews"),
    ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ("War on the Rocks", "https://warontherocks.com/feed/"),
    ("Foreign Policy", "https://foreignpolicy.com/feed/"),
    ("ISW", "https://www.understandingwar.org/rss.xml"),
    ("RAND Corporation", "https://www.rand.org/pubs/rss/research_briefs.xml"),
    # OSINT & Intel
    ("Bellingcat", "https://www.bellingcat.com/feed/"),
    ("The War Zone", "https://www.thedrive.com/the-war-zone/rss"),
    ("Oryx", "https://www.oryxspioenkop.com/feeds/posts/default"),
    # Cyber / Defense Tech
    ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
    # Veteran Affairs
    ("VA News", "https://news.va.gov/feed/"),
]

# ── Bot setup ──────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── RSS Fetching ───────────────────────────────────────────────────────────────
def fetch_headlines() -> str:
    """Fetch recent headlines from all RSS feeds."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    all_headlines = []

    for source_name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()[:200]
                published = entry.get("published", "")
                if title:
                    all_headlines.append(
                        f"[{source_name}] {title}\n{summary}"
                    )
        except Exception as e:
            print(f"⚠️ Failed to fetch {source_name}: {e}")

    if not all_headlines:
        return "No headlines available."

    return "\n\n".join(all_headlines)

# ── AI Brief Generation ────────────────────────────────────────────────────────
def generate_brief(headlines: str) -> str:
    """Use Claude to generate an intel-style daily brief."""
    today = datetime.now().strftime("%d %B %Y").upper()

    prompt = f"""You are a military intelligence analyst writing a daily brief for a military Discord server. 
Based on the following headlines, write a concise, professional intel-style daily brief.

Format it EXACTLY like this:
```
═══════════════════════════════════════
🎺 REVEILLE — DAILY BRIEF
📅 {today} | 0800 EASTERN
═══════════════════════════════════════

EXECUTIVE SUMMARY
[2-3 sentence overview of the most important developments]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🪖 U.S. MILITARY & DoD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• [bullet point]
• [bullet point]
• [bullet point]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌍 GEOPOLITICAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• [bullet point]
• [bullet point]
• [bullet point]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎖️ VETERAN AFFAIRS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• [bullet point]
• [bullet point]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYST NOTE
[1-2 sentence closing observation or item to watch]
═══════════════════════════════════════
```

Keep bullet points concise and factual. Use military terminology where appropriate. Do not editorialize or inject opinion. If a section has no relevant news, write "Nothing significant to report."

HEADLINES:
{headlines}"""

    message = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# ── Events ─────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    daily_brief.start()

# ── Slash Commands ─────────────────────────────────────────────────────────────
@bot.tree.command(name="brief", description="Generate and post today's daily brief right now")
async def brief(interaction: discord.Interaction):
    # Moderator or admin only
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You need Manage Server permission to use this.", ephemeral=True)
        return

    await interaction.response.send_message("📰 Generating brief, stand by...", ephemeral=True)
    await post_brief()

@bot.tree.command(name="briefstatus", description="Check when the next daily brief is scheduled")
async def briefstatus(interaction: discord.Interaction):
    now = datetime.now(timezone.utc)
    target = now.replace(hour=BRIEF_HOUR_UTC, minute=BRIEF_MINUTE_UTC, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    delta = target - now
    hours = int(delta.total_seconds() // 3600)
    minutes = int((delta.total_seconds() % 3600) // 60)
    await interaction.response.send_message(
        f"📅 Next brief posts in **{hours}h {minutes}m** (0800 Eastern).", ephemeral=True
    )

# ── Brief posting ──────────────────────────────────────────────────────────────
async def post_brief():
    channel = bot.get_channel(BRIEF_CHANNEL_ID)
    if not channel:
        print("❌ Could not find brief channel!")
        return

    print("📰 Fetching headlines...")
    headlines = await asyncio.to_thread(fetch_headlines)

    print("🤖 Generating brief with Claude...")
    brief_text = await asyncio.to_thread(generate_brief, headlines)

    # Discord has a 2000 char limit per message — split if needed
    if len(brief_text) <= 2000:
        await channel.send(brief_text)
    else:
        chunks = [brief_text[i:i+1990] for i in range(0, len(brief_text), 1990)]
        for chunk in chunks:
            await channel.send(chunk)

    print("✅ Brief posted!")

# ── Daily task ─────────────────────────────────────────────────────────────────
@tasks.loop(hours=24)
async def daily_brief():
    await post_brief()

@daily_brief.before_loop
async def before_brief():
    await bot.wait_until_ready()
    now = datetime.now(timezone.utc)
    target = now.replace(hour=BRIEF_HOUR_UTC, minute=BRIEF_MINUTE_UTC, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    seconds_to_wait = (target - now).total_seconds()
    hours = int(seconds_to_wait // 3600)
    minutes = int((seconds_to_wait % 3600) // 60)
    print(f"⏰ First brief in {hours}h {minutes}m (0800 Eastern)")
    await asyncio.sleep(seconds_to_wait)

# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN not found!")
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not found!")
    bot.run(DISCORD_TOKEN)