import asyncio
import re
import typing
from collections import defaultdict
import discord
from discord.ext import commands
from .utils.utils import StrictDiscordTextChannel

class Reminder():
    def __init__(self, guild_id, author_id, channel_id, message):
        self.id = id(self)
        self.guild_id = guild_id
        self.author_id = author_id
        self.channel_id = channel_id
        self.message = message
        self.task = None

class ReminderCogCheck():
    @staticmethod
    async def max_reminders(ctx):
        reminder_list = ReminderCog.reminders.get((ctx.guild.id, ctx.author.id))
        if reminder_list is not None and len(reminder_list) == ReminderCog.MAX_REMINDERS:
            raise commands.CheckFailure('max_reminders')
        return True

class ReminderCog(commands.Cog, name='Reminder'):
    reminders = defaultdict(list)
    MAX_REMINDERS = 4
    MESSAGE_CHARACTER_LIMIT = 100

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='remind-me')
    @commands.check(ReminderCogCheck.max_reminders)
    async def remind_me(self, ctx, time, text_channel: typing.Optional[StrictDiscordTextChannel], *, message: commands.clean_content=''):
        # parse the time str before the reminder is stored in case an error is raised
        sleep_seconds, time_display = self.parse_time_str(time)

        if len(message) > ReminderCog.MESSAGE_CHARACTER_LIMIT:
            await ctx.send('Your reminder cannot be more than 100 characters')
            return
        
        channel_id = None
        if text_channel is None:
            channel_id = ctx.channel.id
        elif not text_channel.permissions_for(ctx.guild.me).send_messages or not text_channel.permissions_for(ctx.author).view_channel:
            await ctx.send('I cannot send a reminder to that channel')
            return
        else:
            channel_id = text_channel.id
        
        reminder = Reminder(ctx.guild.id, ctx.author.id, channel_id, message)
        # guarantee that reminder is stored before creating the task for the reminder
        ReminderCog.reminders[(ctx.guild.id, ctx.author.id)].append(reminder)
        reminder.task = self.bot.loop.create_task(self.sleep_reminder(ctx.guild.id, ctx.author.id, reminder.id, sleep_seconds))
        
        await ctx.send(f'Okay I will remind you at <#{channel_id}> in **{time_display}**!')

        print(ReminderCog.reminders)

    @remind_me.error
    async def remind_me_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            if len(error.args) == 0:
                raise error
            
            if error.args[0] == 'max_reminders':
                await ctx.send(f'Reminder not set. You can only have {ReminderCog.MAX_REMINDERS} reminders at a time.')
            else:
                raise error
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify a time for your reminder')
        elif isinstance(error, commands.BadArgument):
            await ctx.send(error)
        else:
            raise error

    @commands.command(name='show-reminders')
    async def show_reminders(self, ctx):
        reminder_list = ReminderCog.reminders.get((ctx.guild.id, ctx.author.id))
        if reminder_list is None:
            await ctx.send('You have no reminders')
        else:
            display = '```python'
            for reminder in reminder_list:
                channel = self.bot.get_channel(reminder.channel_id)
                display += f'\n"{reminder.message}"\n#ID: {reminder.id} | #Channel: #{channel.name}\n'
            await ctx.send(display + '```')

    @commands.command(name='delete-reminder')
    async def delete_reminder(self, ctx):
        pass

    async def cog_check(self, ctx):
        return ctx.guild is not None and ctx.channel.permissions_for(ctx.guild.me).send_messages

    async def sleep_reminder(self, guild_id, author_id, reminder_id, seconds):
        sleep_seconds = seconds
        while sleep_seconds > discord.utils.MAX_ASYNCIO_SECONDS:
            await asyncio.sleep(discord.utils.MAX_ASYNCIO_SECONDS)
            sleep_seconds -= discord.utils.MAX_ASYNCIO_SECONDS
        await asyncio.sleep(sleep_seconds)

        reminder_list = ReminderCog.reminders[(guild_id, author_id)]
        pending_reminder = None
        for reminder in range(len(reminder_list)):
            if reminder_list[reminder].id == reminder_id:
                pending_reminder = reminder_list.pop(reminder)
                break

        channel = self.bot.get_channel(pending_reminder.channel_id)
        await channel.send(f'<@{pending_reminder.author_id}> {pending_reminder.message}')

        print(ReminderCog.reminders)

    def parse_time_str(self, time_str):
        match = re.match(r'^([1-3]w)?([1-6]d)?(([1-9]|1\d|2[0-3])h)?(([1-9]|[1-5]\d)m)?(([1-9]|[1-5]\d)s)?$', time_str)
        if match is None:
            raise commands.BadArgument('The time is not in the correct format')

        conversions = {
            'w': ('weeks', 604800), # 1 week = 604800 seconds
            'd': ('days', 86400),   # 1 day  = 86400 seconds
            'h': ('hours', 3600),   # 1 hour = 3600 seconds
            'm': ('minutes', 60),
            's': ('seconds', 1)
        }

        total_seconds = 0
        time_display = []
        start = 0
        for pos in range(len(time_str)):
            current = time_str[pos]
            if not current.isdigit():
                num = int(time_str[start:pos])
                total_seconds += num * conversions[current][1]
                period = conversions[current][0]
                if num == 1:
                    period = period.rstrip('s')
                time_display.append(f'{num} {period}')
                start += pos + 1

        return (total_seconds, ' '.join(time_display))

def setup(bot):
    bot.add_cog(ReminderCog(bot))