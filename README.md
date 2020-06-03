# Discord Reminder Bot
A Discord Bot for reminders

## Command Prefix
Default: `.`
Example: `.help`

## Command Syntax
`[]` - optional parameter
`<>` - required paramater
Note: some commands take no parameters

## Commands
`.reminder <duration> [channel] [message]` - Creates a reminder
Send a reminder after the specified amount of time (under 10 weeks) to the specified 
channel. If the channel is not specified then the reminder will be sent to the channel 
the command was sent from. You can only have up to 4 reminders at a time.
**Example:**
`.reminder 30m Drink water`
`.reminder 1d #general Drink some more water`

`.list` - Lists all your current reminders
Shows a list of all your current reminders along with their message, ID, channel it 
will be sent to, and how much time until it is sent.

`.delete <id>` - Deletes a reminder
Deletes a reminder with the specifed ID. Use the `.list` command to see a reminder's ID.
**Example:**
`.delete 1234567890` 

`.clear` - Clears all your current reminders
Deletes all your current reminders.

`.edit duration <id> <duration>` - Edits a reminder's duration
Edits a reminder's duration corresponding with the specified reminder ID. The reminder 
will be sent after the new specified duration from when this command is sent. Use the 
`.list` command to see a reminder's ID.
**Example:**
`.edit duration 1234567890 5w`

`.edit channel <id> <channel>` - Edits a reminder's channel
Edits a reminder's channel corresponding with the specified reminder ID. The reminder 
will be sent to the new specified channel. Use the `.list` command to see a reminder's ID.
**Example:**
`.edit channel 1234567890 #general`

`.edit message <id> [message]` - Edits a reminder's message
Edits a reminder's message corresponding with the specified reminder ID. The reminder 
will be sent with the new specified message. Use the `.list` command to see a reminder's ID.
**Example:**
`.edit message 1234567890 Drink milk`

`.help [command]` - Shows the help message
Use this command to get help on how to use the bot and its commands.

## Requirements
- Python 3.6+
- discord.py v1.0.0