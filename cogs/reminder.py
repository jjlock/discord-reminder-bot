import asyncio
import datetime
import textwrap
import typing
from collections import defaultdict
import discord
from discord.ext import commands
from .utils.converters import Duration, TextChannelMention

class Reminder():
    def __init__(self, author_id, channel_id, created, expires, message):
        self.id = id(self)
        self.author_id = author_id
        self.channel_id = channel_id
        self.created = created
        self.expires = expires
        self.message = message
        self.task = None

class ReminderCog(commands.Cog, name='Reminder'):
    """Reminders for people on Discord"""
    
    reminders = defaultdict(dict)
    MAX_REMINDERS = 4

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None and ctx.channel.permissions_for(ctx.guild.me).send_messages

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'You are missing one or more arguments for the {ctx.command.name} command')
        else:
            raise error

    def has_max_reminders(self, guild_id, author_id):
        reminder_dict = ReminderCog.reminders.get((guild_id, author_id))
        return reminder_dict is not None and len(reminder_dict) == ReminderCog.MAX_REMINDERS

    def get_reminder(self, guild_id, author_id, reminder_id):
        reminder_dict = ReminderCog.reminders.get((guild_id, author_id))
        if not reminder_dict:
            return None

        return reminder_dict.get(reminder_id)

    def pop_reminder(self, guild_id, author_id, reminder_id):
        reminder_dict = ReminderCog.reminders.get((guild_id, author_id))
        if not reminder_dict:
            return None
        
        return reminder_dict.pop(reminder_id, None)

    async def send_reminder(self, guild_id, author_id, reminder_id, seconds):
        # discord.py caps asyncio.sleep to 40 days since asyncio.sleep can 
        # only sleep up to ~48 days reliably
        while seconds > discord.utils.MAX_ASYNCIO_SECONDS:
            await asyncio.sleep(discord.utils.MAX_ASYNCIO_SECONDS)
            seconds -= discord.utils.MAX_ASYNCIO_SECONDS
        await asyncio.sleep(seconds)

        reminder = self.pop_reminder(guild_id, author_id, reminder_id)
        if reminder is not None:
            channel = self.bot.get_channel(reminder.channel_id)
            await channel.send(f'<@{reminder.author_id}> {reminder.message}')

        print(ReminderCog.reminders)
    
    @commands.command(aliases=['remind', 'remind-me'])
    async def reminder(self, ctx, duration: Duration, send_to: typing.Optional[TextChannelMention], *, message: commands.clean_content(fix_channel_mentions=True)=''):
        """
        Creates a reminder

        duration: When the reminder should be sent from now in weeks, days, hours, minutes, and/or seconds.
        The duration must be under 10 weeks.
        Examples:
            1d = 1 day
            6h50s = 6 hours 50 seconds
            5w3d12h30m30s = 5 weeks 3 days 12 hours 30 minutes 30 seconds

        send_to: The channel to send the reminder to. If not specified, then the reminder will be sent to 
        the channel the command was sent from. If specified, it must be given as a text channel mention.
        
        message: The message for the reminder. Mentions will be sent as their scrubbed versions.

        You can only have up to 4 reminders at a time.
        """
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

        # if the duration is equal to 0 seconds then send the message immediately
        if duration.seconds == 0:
            await channel.send(f'<@{ctx.author.id}> {message}')
            return
        
        reminder = Reminder(ctx.author.id, channel.id, ctx.message.created_at, duration.end, message)

        # the reminder should be stored before creating the task for the reminder
        ReminderCog.reminders[(ctx.guild.id, ctx.author.id)][reminder.id] = reminder
        reminder.task = self.bot.loop.create_task(self.send_reminder(ctx.guild.id, ctx.author.id, reminder.id, duration.seconds))
        
        await ctx.send(f'Okay I will remind you at <#{channel.id}> in **{Duration.display(duration.seconds)}**!')

        print(ReminderCog.reminders)

    @commands.command(name='list', aliases=['list-reminders'])
    async def list_reminders(self, ctx):
        """Lists all your current reminders"""
        reminder_dict = ReminderCog.reminders.get((ctx.guild.id, ctx.author.id))
        if not reminder_dict:
            await ctx.send('You have no reminders')
            return
        
        display = '```python'
        for reminder in sorted(reminder_dict.values(), key=lambda reminder: reminder.created):
            shortened = textwrap.shorten(reminder.message, width=100)
            channel = ctx.guild.get_channel(reminder.channel_id)
            remaining = int((reminder.expires - datetime.datetime.utcnow()).total_seconds())
            display += f'\n"{shortened}"\n#ID: {reminder.id} | Channel: #{channel.name} | In: {Duration.display(remaining, granularity=2)}\n'
        await ctx.send(display + '```')

    @commands.command(name='delete', aliases=['delete-reminder'])
    async def delete_reminder(self, ctx, id: int):
        """
        Deletes a reminder with the given ID
        
        The ID can be found using the list command

        You can only delete your own reminders
        """
        reminder = self.pop_reminder(ctx.guild.id, ctx.author.id, id)
        if reminder is None:
            await ctx.send('I could not find a reminder with that ID')
            return

        reminder.task.cancel()
        await ctx.send('Reminder deleted')

    @commands.command(name='clear', aliases=['clear-reminders'])
    async def clear_reminders(self, ctx):
        """Deletes all your reminders"""
        reminder_dict = ReminderCog.reminders.get((ctx.guild.id, ctx.author.id))
        if not reminder_dict:
            await ctx.send('You have no reminders to delete')
            return
        
        for reminder in reminder_dict.values():
            reminder.task.cancel()

        reminder_dict.clear()
        await ctx.send('All your reminders are deleted')

    @commands.group(name='edit', aliases=['edit-reminder'])
    async def edit_reminder(self, ctx):
        """
        Commands for editing your reminders
        
        The ID can be found with the list command

        You can only edit your own reminders
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f'{ctx.subcommand_passed} is not a subcommand of the {ctx.command.name} command')

    @edit_reminder.command(name='duration', aliases=['time'])
    async def edit_reminder_duration(self, ctx, id: int, duration: Duration):
        """Edits the duration of a reminder with the given ID"""
        reminder = self.get_reminder(ctx.guild.id, ctx.author.id, id)
        if reminder is None:
            await ctx.send('I could not find a reminder with that ID')
            return
        
        reminder.task.cancel()
        reminder.expires = duration.end
        reminder.task = self.bot.loop.create_task(self.send_reminder(ctx.guild.id, ctx.author.id, reminder.id, duration.seconds))
        await ctx.send(f'Okay I will now remind you in **{Duration.display(duration.seconds)}**')

    @edit_reminder.command(name='channel', aliases=['dest', 'destination'])
    async def edit_reminder_channel(self, ctx, id: int, channel: discord.TextChannel):
        """Edits the channel the reminder with the given ID should be sent to"""
        reminder = self.get_reminder(ctx.guild.id, ctx.author.id, id)
        if reminder is None:
            await ctx.send('I could not find a reminder with that ID')
            return

        if not channel.permissions_for(ctx.guild.me).send_messages or not channel.permissions_for(ctx.author).view_channel:
                await ctx.send('I cannot send a reminder to that channel')
                return

        reminder.channel_id = channel.id
        await ctx.send(f'Okay I will now remind you at <#{reminder.channel_id}>')

    @edit_reminder.command(name='message', aliases=['msg'])
    async def edit_reminder_message(self, ctx, id: int, *, message):
        """Edits the message of a reminder with the given ID"""
        reminder = self.get_reminder(ctx.guild.id, ctx.author.id, id)
        if reminder is None:
            await ctx.send('I could not find a reminder with that ID')
            return

        reminder.message = message
        await ctx.send("Okay I changed your reminder's message")

def setup(bot):
    """Adds the Reminder cog to the bot."""
    bot.add_cog(ReminderCog(bot))