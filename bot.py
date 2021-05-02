import json
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print('Bot is ready')

# Extensions
bot.load_extension('cogs.reminder')

# Configuration
load_dotenv()

bot.run(os.getenv('DISCORD_BOT_TOKEN'))