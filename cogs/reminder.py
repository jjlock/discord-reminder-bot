import asyncio
import textwrap
import typing
from collections import defaultdict
import discord
from discord.ext import commands
from .utils.converters import Duration, TextChannelMention

class Reminder():
    def __init__(self, guild_id, author_id, channel_id, message):
        self.id = id(self)
        self.author_id = author_id
        self.channel_id = channel_id
        self.message = message
        self.task = None

class ReminderCog(commands.Cog, name='Reminder'):
    reminders = defaultdict(list)
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
        elif isinstance(error, commands.TooManyArguments):
            await ctx.send(f'You used the {ctx.command.name} command with too many arguments')
        else:
            raise error
    
    @commands.command(aliases=['remind', 'remind-me'])
    async def reminder(self, ctx, duration: Duration, send_to: typing.Optional[TextChannelMention], *, message: commands.clean_content(fix_channel_mentions=True)=''):
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

    @commands.command(name='list', aliases=['list-reminders'])
    async def list_reminders(self, ctx):
        reminder_list = ReminderCog.reminders.get((ctx.guild.id, ctx.author.id))
        if not reminder_list:
            await ctx.send('You have no reminders')
        else:
            display = '```python'
            for reminder in reminder_list:
                shortened = textwrap.shorten(reminder.message, width=100)
                channel = ctx.guild.get_channel(reminder.channel_id)
                display += f'\n"{shortened}"\n#ID: {reminder.id} | Channel: #{channel.name}\n'
            await ctx.send(display + '```')

    @commands.command(name='delete', aliases=['delete-reminder'])
    async def delete_reminder(self, ctx, id: int):
        index = self.reminder_index(ctx.guild.id, ctx.author.id, id)
        
        if index is None:
            await ctx.send('I could not find a reminder with that ID')
            return

        reminder = ReminderCog.reminders[(ctx.guild.id, ctx.author.id)].pop(index)
        reminder.task.cancel()
        await ctx.send('Reminder deleted')

    @commands.command(name='clear', aliases=['clear-reminders'])
    async def clear_reminders(self, ctx):
        reminder_list = ReminderCog.reminders.get((ctx.guild.id, ctx.author.id))

        if not reminder_list:
            await ctx.send('You have no reminders to delete')
            return
        
        for reminder in reminder_list:
            reminder.task.cancel()
       
        reminder_list.clear()
        await ctx.send('All your reminders are deleted')

    @commands.group(name='edit', aliases=['edit-reminder'])
    async def edit_reminder(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f'{ctx.subcommand_passed} is not a subcommand of the {ctx.command.name} command')

    @edit_reminder.command(name='time', aliases=['duration'])
    async def edit_reminder_time(self, ctx, id: int, duration: Duration):
        index = self.reminder_index(ctx.guild.id, ctx.author.id, id)

        if index is None:
            await ctx.send('I could not find a reminder with that ID')
            return

        reminder = ReminderCog.reminders[(ctx.guild.id, ctx.author.id)][index]
        reminder.task.cancel()
        reminder.task = self.bot.loop.create_task(self.send_reminder(ctx.guild.id, ctx.author.id, reminder.id, duration.seconds))
        await ctx.send(f'Okay I will now remind you in **{duration.display}**')

    @edit_reminder.command(name='channel', aliases=['dest', 'destination'])
    async def edit_reminder_channel(self, ctx, id: int, channel: discord.TextChannel):
        index = self.reminder_index(ctx.guild.id, ctx.author.id, id)

        if index is None:
            await ctx.send('I could not find a reminder with that ID')
            return

        if not channel.permissions_for(ctx.guild.me).send_messages or not channel.permissions_for(ctx.author).view_channel:
                await ctx.send('I cannot send a reminder to that channel')
                return

        reminder = ReminderCog.reminders[(ctx.guild.id, ctx.author.id)][index]
        reminder.channel_id = channel.id
        await ctx.send(f'Okay I will now remind you at <#{reminder.channel_id}>')

    @edit_reminder.command(name='message', aliases=['msg'])
    async def edit_reminder_message(self, ctx, id: int, *, message):
        index = self.reminder_index(ctx.guild.id, ctx.author.id, id)

        if index is None:
            await ctx.send('I could not find a reminder with that ID')
            return

        reminder = ReminderCog.reminders[(ctx.guild.id, ctx.author.id)][index]
        reminder.message = message
        await ctx.send("Okay I changed your reminder's message")

    async def send_reminder(self, guild_id, author_id, reminder_id, seconds):
        while seconds > discord.utils.MAX_ASYNCIO_SECONDS:
            await asyncio.sleep(discord.utils.MAX_ASYNCIO_SECONDS)
            seconds -= discord.utils.MAX_ASYNCIO_SECONDS
        await asyncio.sleep(seconds)

        index = self.reminder_index(guild_id, author_id, reminder_id)
        reminder = ReminderCog.reminders[(guild_id, author_id)].pop(index)
        channel = self.bot.get_channel(reminder.channel_id)
        await channel.send(f'<@{reminder.author_id}> {reminder.message}')

        print(ReminderCog.reminders)

    def has_max_reminders(self, guild_id, author_id):
        reminder_list = ReminderCog.reminders.get((guild_id, author_id))
        return reminder_list is not None and len(reminder_list) == ReminderCog.MAX_REMINDERS

    def reminder_index(self, guild_id, author_id, reminder_id):
        reminder_list = ReminderCog.reminders.get((guild_id, author_id))
        
        if not reminder_list:
            return None
        
        index = next((i for i, reminder in enumerate(reminder_list) if reminder.id == reminder_id), None)
        
        return index

def setup(bot):
    bot.add_cog(ReminderCog(bot))