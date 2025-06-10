import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import io
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Import your existing analysis functions
from damage_log import DamageLog
from damage_taken_log import DmgRecLog
# ...existing imports...

class LogCache:
    def __init__(self):
        self.current_log = None
        self.log_path = None
        self.expiry_time = None
        self.duration_hours = 2  # Cache duration in hours

    async def set_log(self, attachment):
        # Save new log file
        if self.log_path and os.path.exists(self.log_path):
            os.remove(self.log_path)
            
        self.log_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        await attachment.save(self.log_path)
        self.expiry_time = datetime.now() + timedelta(hours=self.duration_hours)
        return self.log_path

    def get_log(self):
        if not self.log_path or not os.path.exists(self.log_path):
            return None
        if datetime.now() > self.expiry_time:
            os.remove(self.log_path)
            self.log_path = None
            return None
        return self.log_path

    def clear(self):
        if self.log_path and os.path.exists(self.log_path):
            os.remove(self.log_path)
        self.log_path = None
        self.expiry_time = None

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
log_cache = LogCache()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='loadlog')
async def load_log(ctx):
    """Load a log file into memory for analysis"""
    if not ctx.message.attachments:
        await ctx.send("Please attach a log file!")
        return

    try:
        attachment = ctx.message.attachments[0]
        log_path = await log_cache.set_log(attachment)
        await ctx.send(f"Log file loaded! It will be available for {log_cache.duration_hours} hours.\nUse !help to see available commands.")
    except Exception as e:
        await ctx.send(f"Error loading log: {str(e)}")

@bot.command(name='damage')
async def damage(ctx):
    """Generate damage plot from cached log"""
    log_path = log_cache.get_log()
    if not log_path:
        await ctx.send("No log file loaded! Use !loadlog to load a log file first.")
        return

    try:
        _, plot = DamageLog(log_path, (0, 24), includePvE=0)
        buf = io.BytesIO()
        plot.savefig(buf, format='png')
        buf.seek(0)
        await ctx.send(file=discord.File(buf, 'damage.png'))
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")
    finally:
        plt.close('all')

@bot.command(name='help')
async def help_command(ctx):
    help_text = """
    **Available Commands:**
    !loadlog - Load a new log file (attach the file)
    !damage - Overall damage done
    !damagetaken - Damage taken
    !healing - Healing done
    !combos - Track combo usage
    !casts - Track important ability casts
    !pots - Healing from potions
    !songs - Song buff uptime
    !debuffs - Song debuff uptime
    !mend - Mend healing analysis
    
    The loaded log file expires after 2 hours.
    """
    await ctx.send(help_text)

# Add similar commands for other analysis types...

bot.run(os.getenv('DISCORD_TOKEN'))
