import json
import os
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    print('Bot is ready')

# Extensions
bot.load_extension('cogs.reminder')

# Configuration
config_file = None
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json'), 'r') as file:
    config_file = json.load(file)

bot.run(config_file['token'])