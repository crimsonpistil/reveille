import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import json
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
SEEN_FILE = "/data/seen.json"
SEEN_EXPIRY_DAYS = 7

# ── RSS Feed Sources ───────────────────────────────────────────────────────────
RSS_FEEDS = [
    # --- US Military & DoD ---
    ("Defense One", "https://www.defenseone.com/rss/all/"),
    ("Military Times", "https://www.militarytimes.com/arc/outboundfeeds/rss/"),
    ("DoD News", "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10"),
    ("Stars and Stripes", "https://www.stripes.com/arc/outboundfeeds/rss/"),
    ("Defense News", "https://www.defensenews.com/arc/outboundfeeds/rss/"),
    ("Task & Purpose", "https://taskandpurpose.com/feed/"),
    ("Breaking Defense", "https://breakingdefense.com/feed/"),

    # --- Geopolitics & Think Tanks ---
    ("War on the Rocks", "https://warontherocks.com/feed/"),
    ("Foreign Policy", "https://foreignpolicy.com/feed/"),
    ("ISW", "https://www.understandingwar.org/rss.xml"),
    ("RAND Corporation", "https://www.rand.org/pubs/rss/research_briefs.xml"),
    ("Small Wars Journal", "https://smallwarsjournal.com/rss.xml"),

    # --- Intelligence & OSINT ---
    ("Recorded Future - The Record", "https://therecord.media/feed/"),
    ("Recorded Future - Insikt Group", "https://www.recordedfuture.com/research/insikt-group/feed"),
    ("Bellingcat", "https://www.bellingcat.com/feed/"),
    ("The War Zone", "https://www.twz.com/feed"),
    ("Oryx", "https://www.oryxspioenkop.com/feeds/posts/default"),
    ("CISA Alerts", "https://www.cisa.gov/cybersecurity-advisories/all.xml"),
    ("ODNI News", "https://www.dni.gov/index.php/newsroom/press-releases?format=feed&type=rss"),

    # --- Cyber & Vet Affairs ---
    ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
    ("VA News", "https://news.va.gov/feed/"),
]

# ── Bot setup ──────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── Seen articles tracker ──────────────────────────────────────────────────────
def load_seen() -> dict:
    """Load seen article URLs with timestamps."""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_seen(data: dict):
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f, indent=2)

def prune_seen(data: dict) -> dict:
    """Remove entries older than SEEN_EXPIRY_DAYS."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=SEEN_EXPIRY_DAYS)).isoformat()
    return {url: ts for url, ts in data.items() if ts >= cutoff}

def mark_seen(urls: list):
    """Mark a list of URLs as seen."""
    data = load_seen()
    data = prune_seen(data)
    now = datetime.now(timezone.utc).isoformat()
    for url in urls:
        data[url] = now
    save_seen(data)

# ── RSS Fetching ───────────────────────────────────────────────────────────────
def fetch_headlines() -> tuple[str, list]:
    """
    Fetch new headlines from all RSS feeds.
    Returns (formatted headlines string, list of seen URLs to mark).
    """
    seen = load_seen()
    seen = prune_seen(seen)

    all_headlines = []
    new_urls = []

    for source_name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()[:200]
                link = entry.get("link", "").strip()

                if not title or not link:
                    continue

                # Skip if already seen
                if link in seen:
                    continue

                all_headlines.append(f"[{source_name}] {title}\n{summary}")
                new_urls.append(link)

        except Exception as e:
            print(f"⚠️ Failed to fetch {source_name}: {e}")

    if not all_headlines:
        return "No new headlines since last brief.", []

    print(f"📰 Found {len(all_headlines)} new articles across {len(RSS_FEEDS)} feeds")
    return "\n\n".join(all_headlines), new_urls

# ── AI Brief Generation ────────────────────────────────────────────────────────
def generate_brief(headlines: str) -> str:
    """Use Claude to generate an intel-style daily brief."""
    today = datetime.now().strftime("%d %B %Y").upper()

    prompt = f"""You are a military intelligence analyst writing a daily brief for a military Discord server. 
Based on the following headlines, write a concise, professional intel-style daily brief.

Format it EXACTLY like this:

═══════════════════════════════════════
REVEILLE -- DAILY BRIEF
{today} | 0800 EASTERN
═══════════════════════════════════════

EXECUTIVE SUMMARY
[2-3 sentence overview of the most important developments across all categories]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
U.S. MILITARY & DOD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- [bullet point]
- [bullet point]
- [bullet point]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GEOPOLITICS & THINK TANKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- [bullet point]
- [bullet point]
- [bullet point]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTELLIGENCE & OSINT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- [bullet point]
- [bullet point]
- [bullet point]


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CYBER & VETERAN AFFAIRS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- [bullet point]
- [bullet point]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYST NOTE
[1-2 sentence closing observation or item to watch]
═══════════════════════════════════════

Keep bullet points concise and factual. The entire brief must fit within 1800 characters total. Use military terminology where appropriate. Do not editorialize or inject opinion. If a section has no relevant news, write "NSTR". Do not use emojis anywhere in the brief. 

HEADLINES:
{headlines}"""

    message = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
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

    print("📰 Fetching new headlines...")
    headlines, new_urls = await asyncio.to_thread(fetch_headlines)

    if not new_urls:
        print("ℹ️ No new articles found — skipping brief.")
        await channel.send("No new stories since the last brief. Check back tomorrow!")
        return

    print(f"🤖 Generating brief with Claude ({len(new_urls)} new articles)...")
    brief_text = await asyncio.to_thread(generate_brief, headlines)

    # Post the brief
    if len(brief_text) <= 2000:
        message = await channel.send(brief_text)
    else:
        chunks = [brief_text[i:i+1990] for i in range(0, len(brief_text), 1990)]
        message = None
        for chunk in chunks:
            message = await channel.send(chunk)

    # Create a discussion thread on the last message
    today = datetime.now().strftime("%d %b %Y").upper()
    await message.create_thread(
        name=f"DISCUSSION -- {today}",
        auto_archive_duration=1440  # Auto-archive after 24 hours
    )

    # Mark all new articles as seen AFTER successful post
    mark_seen(new_urls)
    print(f"✅ Brief posted with discussion thread! Marked {len(new_urls)} articles as seen.")

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
