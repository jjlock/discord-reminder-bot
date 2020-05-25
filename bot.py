import json
import os
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='.')
current_dir = os.path.dirname(os.path.abspath(__file__))
config_file = None

for filename in os.listdir(current_dir + '/cogs/'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

with open(current_dir + '/config.json', 'r') as file:
    config_file = json.load(file)

@bot.event
async def on_ready():
    print('Bot is ready')

bot.run(config_file['token'])