import re
import discord
from discord.ext import commands

class StrictDiscordTextChannel(commands.Converter):
    # checks if argument is a discord.TextChannel and if it is not then prevent argument from casting to discord.TextChannel
    async def convert(self, ctx, argument):
        match = re.match(r'<#([0-9]+)>$', argument)
        if match is None:
            # not a mention
            raise commands.BadArgument(f'{argument} is not a TextChannel')
        
        channel = ctx.guild.get_channel(int(match.group(1)))
        
        if not isinstance(channel, discord.TextChannel):
            raise commands.BadArgument(f'Channel {argument} not found')
        
        return channel