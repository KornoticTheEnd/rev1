import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import io
import matplotlib.pyplot as plt

# Import all analysis functions
from damage_log import DamageLog
from damage_taken_log import DmgRecLog
from healing_log import HealingLog
from combo_tracker import ComboTracker, plot_combo_results
from cast_tracker import CastTracker, plot_cast_results
from damage_by_ability import DmgAbiLog
from healing_taken_target import HealReceivedByPlayer
from healing_pots import PotsLog
from mend import parse_heal_log, calculate_heal_stats, plot_total_heals
from song_buff import plot_song_buff_data
from song_debuffs import plot_song_debuff_data

# Load token and set up bot
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ALLOWED_CHANNELS = os.getenv('ALLOWED_CHANNELS', '').split(',')  # Add allowed channel IDs in .env

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def check_channel(ctx):
    """Check if command is used in allowed channel"""
    return str(ctx.channel.id) in ALLOWED_CHANNELS

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='help')
async def help_command(ctx):
    """Show available commands"""
    if not check_channel(ctx):
        return
        
    help_text = """
    **Available Commands:**
    !damage - Overall damage done
    !damagetaken - Damage taken
    !healing - Healing done
    !combos - Track combo usage
    !casts - Track important ability casts
    !pots - Healing from potions
    !songs - Song buff uptime
    !debuffs - Song debuff uptime
    !mend - Mend healing analysis
    
    Add a player name for specific analysis:
    !damage_by [player]
    !damagetaken_by [player]
    !healing_by [player]
    
    All commands require an attached log file.
    """
    await ctx.send(help_text)

# ... existing damage command ...

@bot.command(name='damagetaken')
async def damage_taken(ctx):
    """Generate damage taken plot"""
    if not check_channel(ctx):
        return
        
    if not ctx.message.attachments:
        await ctx.send("Please attach a log file!")
        return

    try:
        attachment = ctx.message.attachments[0]
        await attachment.save("temp.log")
        _, plot = DmgRecLog("temp.log", 25, includePvE=0)
        buf = io.BytesIO()
        plot.savefig(buf, format='png')
        buf.seek(0)
        await ctx.send(file=discord.File(buf, 'damage_taken.png'))
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")
    finally:
        if os.path.exists("temp.log"):
            os.remove("temp.log")
        plt.close('all')

# Add more commands for other analysis types...

bot.run(TOKEN)
