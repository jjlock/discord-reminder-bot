import datetime
import re
import discord
from discord.ext import commands

class TextChannelMention(commands.Converter):
    # checks if argument is a text channel mention and if it is not then prevent argument from casting to discord.TextChannel
    async def convert(self, ctx, argument):
        match = re.match(r'<#([0-9]+)>$', argument)
        if match is None:
            raise commands.BadArgument(f'{argument} is not a text channel mention')
        
        channel = ctx.guild.get_channel(int(match.group(1)))
        
        if not isinstance(channel, discord.TextChannel):
            raise commands.BadArgument(f'Channel {argument} not found')
        
        return channel

class Duration(commands.Converter):
    def __init__(self, seconds=0, end=datetime.datetime.utcnow()):
        self.seconds = seconds
        self.end = end

    @classmethod
    async def convert(cls, ctx, argument):
        match = re.fullmatch(r"""(?:(?P<weeks>\d)w)?                # ex: 5w
                                 (?:(?P<days>[0-6])d)?              # ex: 3d
                                 (?:(?P<hours>\d|1\d|2[0-3])h)?     # ex: 12h
                                 (?:(?P<minutes>\d|[1-5]\d)m)?      # ex: 30m
                                 (?:(?P<seconds>\d|[1-5]\d)s)?      # ex: 15s
                              """, argument, re.VERBOSE)
        
        if match is None or not match.group(0):
            raise commands.BadArgument('The duration for the reminder is not in the correct format or is not under 10 weeks')

        data = { interval: int(num) for interval, num in match.groupdict(default=0).items() }
        delta = datetime.timedelta(**data)
        seconds = int(delta.total_seconds())
        end = ctx.message.created_at + delta
        
        return cls(seconds, end)

    @staticmethod
    def display(seconds):
        conversions = (
            ('weeks', 604800),  # 1 week = 604800 seconds
            ('days', 86400),    # 1 day  = 86400 seconds
            ('hours', 3600),    # 1 hour = 3600 seconds
            ('minutes', 60), 
            ('seconds', 1)
        )

        result = []
        for interval, value in conversions:
            num = seconds // value
            if num:
                seconds -=  num * value
                if num == 1:
                    interval = interval.rstrip('s')
                result.append(f'{num} {interval}')

        return ' '.join(result)