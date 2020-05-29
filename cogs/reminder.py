import asyncio
import re
import textwrap
import typing
from collections import defaultdict
import discord
from discord.ext import commands
from .utils.converters import Duration, TextChannelMention

class Reminder():
    def __init__(self, guild_id, author_id, channel_id, message):
        self.id = id(self)
        self.guild_id = guild_id
        self.author_id = author_id
        self.channel_id = channel_id
        self.message = message
        self.task = None

class ReminderCog(commands.Cog, name='Reminder'):
    reminders = defaultdict(list)
    MAX_REMINDERS = 4
    MESSAGE_CHARACTER_LIMIT = 100

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None and ctx.channel.permissions_for(ctx.guild.me).send_messages

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'You are missing one or more arguments for the {ctx.command.name} command')
        elif isinstance(error, commands.TooManyArguments):
            await ctx.send(f'You used the {ctx.command.name} command with too many arguments')
        else:
            raise error
    
    @commands.command(name='remind-me')
    async def remind_me(self, ctx, duration: Duration, send_to: typing.Optional[TextChannelMention], *, message: commands.clean_content(fix_channel_mentions=True)=''):
        if self.has_max_reminders(ctx.guild.id, ctx.author.id):
            await ctx.send(f'Reminder not set. You can only have {ReminderCog.MAX_REMINDERS} reminders at a time.')
            return
        
        channel = None
        
        if send_to is None:
            channel = ctx.channel
        else:
            if not send_to.permissions_for(ctx.guild.me).send_messages or not send_to.permissions_for(ctx.author).view_channel:
                await ctx.send('I cannot send a reminder to that channel')
                return
            channel = send_to

        if duration.seconds == 0:
            await channel.send(f'<@{ctx.author.id}> {message}')
            return
        
        reminder = Reminder(ctx.guild.id, ctx.author.id, channel.id, message)

        # guarantee that the reminder is stored before creating the task for the reminder
        ReminderCog.reminders[(ctx.guild.id, ctx.author.id)].append(reminder)
        reminder.task = self.bot.loop.create_task(self.send_reminder(ctx.guild.id, ctx.author.id, reminder.id, duration.seconds))
        
        await ctx.send(f'Okay I will remind you at <#{channel.id}> in **{duration.display}**!')

        print(ReminderCog.reminders)

    @commands.command(name='show-reminders')
    async def show_reminders(self, ctx):
        reminder_list = ReminderCog.reminders.get((ctx.guild.id, ctx.author.id))
        if reminder_list is None:
            await ctx.send('You have no reminders')
        else:
            display = '```python'
            for reminder in reminder_list:
                shortened = textwrap.shorten(reminder.message, width=100)
                channel = self.bot.get_channel(reminder.channel_id)
                display += f'\n"{shortened}"\n#ID: {reminder.id} | Channel: #{channel.name}\n'
            await ctx.send(display + '```')

    @commands.command(name='delete-reminder')
    async def delete_reminder(self, ctx):
        pass

    async def send_reminder(self, guild_id, author_id, reminder_id, seconds):
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

    def has_max_reminders(self, guild_id, author_id):
        reminder_list = ReminderCog.reminders.get((guild_id, author_id))
        return reminder_list is not None and len(reminder_list) == ReminderCog.MAX_REMINDERS

def setup(bot):
    bot.add_cog(ReminderCog(bot))