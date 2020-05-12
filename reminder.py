import json
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    print('Bot is ready')

with open('config.json', 'r') as file:
    config = json.load(file)

bot.run(config['token'])
