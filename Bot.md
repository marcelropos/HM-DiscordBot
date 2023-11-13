# Bot Design

## Bot Framework

The Bot will use [poise](https://github.com/serenity-rs/poise) that itself uses [serenity](https://github.com/serenity-rs/serenity).

The reason why we use poise instead of directly using serenity is the support for slash/text commands in poise that is similar to [discord.py](https://github.com/Rapptz/discord.py).

## Keyword explanation

* `subject (group)` : A subject is a course at the university (example: "Analysis")
* `study group` : A study group can mean 2 things
  * First is a general study group without a semester number. This represents one degree that a student is able to study (example: "Informatik")
  * Second is a specific study group with a semester. In that case it represents a year inside a degree (example: "IF3")
* `tmpc` : Temporary voice channel

## Storage

The bot will store its data in 3 different places:

### Environment variables

These should store information that the bot will need to operate but will always be the same no matter the guild or state of the bot.

Following will be stored here:

* Bot token
* Database connection details
* Main guild id (The main guild id is used to send start up fail messages and also messages to the bot admins). In the main guild, the admins of the guild are the bot admins.
* Logger levels
* University email domain
* Email SMTP Connection settings to send emails

### Database

For the details of the Database see [here](Database.md).

### Redis

For the details of redis see [here](Redis.md).

## Logging

The Bot should log everything that it does and save it to a file. Also there should be the option to send the log to a discord channel (guild owners can pipe their own log to their channel, the Main guild can receive everything from every server). For this, we will use [tracing](https://github.com/tokio-rs/tracing).

## Bot Features

Here described are all the features that the bot will need to have.

Slash commands will not be used for admin commands. Mod commands can use slash commands if the autocomplete helps.

It is also important that every command has some kind of feedback to the user.

### Setup

Type: Prefix command

Permission: Guild admin

This is used to set all the information for the bot to work in the guild. While the setup is not done, other commands are not available in this guild.

Following information need to be set in the Setup:

* The categories for the subject-, group-, study- and gaming-channels.
* The kick ghost information
  * kick deadline
  * warning deadline
  * time at which the ghosts are checked
  * list of safe roles where users with any of those roles are not ghosts
* channel ids
  * debug channel
  * bot chat channel
  * help chat channel
  * study channel category
  * subject channel category
* role ids
  * studenty role
  * moderator role
  * newsletter role
  * nsfw role
  * study roles separator role
  * subject roles separator role
  * friend role
  * alumni roles separator role
  * alumni role
* TMPC channel keep time

To change any of those settings after the initial setup, one can redo the command and leave the setting that shouldn't be changed blank.

There will be a subcommand to print all the setup information for the guild.

### Help

Type: Prefix command

Permission: Everyone

The help message will need to be build manually as poise doesn't have a nice help message system as discord.py with [discord-pretty-help](https://github.com/casuallycalm/discord-pretty-help).

Idea is to replicate the discord-pretty-help help page 1:1 with the buttons. For this, a kind a modular system need to be designed so that information can be easily added/removed and changed depending on the user permissions.

The help information can easily be gotten from the [command](https://docs.rs/poise/latest/poise/macros/attr.command.html) type. Also additional information can be given with the `custom_data` property of the command macro.

### Tmp Studenty

Type: Prefix command

Permission: Guild admin

Add / Remove a tmp studenty role so that new users get direct access to the server.

### Upgrade

Type: Prefix command

Permission: Guild admin

This command will be disabled by default and also needs a confirmation by one of the bot admins to be sure that not too many upgrades at once are started.

The Upgrade needs to do following:

* Disable all other commands
* Remove subject roles from students
* Recreate the subject text channels
* Rename study groups to one semester up
* Create first semester study groups
* Remap study group - subject links
* Assign students to their default subject roles
* Enable back commands and disable itself

### Alumni

Type: Slash command, Prefix command

Permission: Student above 6. Semester

Mark itself as an alumni. For more info see [here](Alumni.md).

### En/Disable Command

Type: Prefix command

Permission: Guild admin

Enable / Disable Commands. This will be done by saving the list of disabled commands in the database on a per guild basis.

### Shutdown

Type: Prefix command

Permission: Bot admin

Shutdown the bot gracefully.

### Study group role self assignment

Type: Slash command, Prefix command

Permission: Verified student

Assign itself to one of the study groups, only first semester is allowed.

### Grant study group role

Type: Slash command, Prefix command

Permission: Moderator

Assign student to one of the study groups, no matter the semester.

### Create new study group

Type: Prefix command

Permission: Guild admin

Creates a new group up to the semester specified with the color specified.

### Add study group semester to existing study group

Type: Prefix command

Permission: Guild admin

Create a new group with the specified semester. The group must already exist.

### Edit study group

Type: Prefix command

Permission: Guild admin

Edit the role id and channel id of a specific study group. This is used in case the chat of role needs to be replaced by and existing chat or role.

### Delete study group

Type: Prefix command

Permission: Guild admin

Delete a whole study groups with all its semesters. This should only be possible if no users are in that study group

### (De)Activate study group

Type: Prefix command

Permission: Guild admin

Be able to (de)activate a whole study group. In that case students can't register them self into that study group, moderators still can.

### Permanently deactivate study group

Type: Prefix command

Permission: Guild admin

Be able to permanently deactivate a whole study group. The difference between the normal deactivate is that now, no new study groups are being made on upgrade and no new users can be assigned, even by mods.

### Setup log pipe

Type: Prefix command

Permission: Guild admin, bot admin

Pipe the log of the bot for this guild into the channel where the command was made. A second call to this function into the same channel will deactivate the pipe. Only one channel per guild be be used to pipe the logs.

If used in the main guild, every log from every guild will be piped into the channel.

### Kick Ghost

Loop, not a command.

If activated (in the config), every day on the specified time, the bot will kick/warn users that are not verified.

### Show ghosts

Type: Prefix command

Permission: Guild admin

Show a list of ghosts that would be kicked/warned at this moment in time (can also be used if kick ghosts is disabled)

### Verify user

Type: Context Menu Command, Slash command, Prefix command

Permission: Moderator

Adds the studenty role to that Student. It will also verify that user on any other server with the Bot where the student is.

### Verify itself

Type: Slash command, Prefix command

Permission: Not verified students

This command consists of 2 subcommands:

1. Initialize the verification by giving the University issued email and sending a code to that email address
2. Give the code received by email. If the code is correct for that user, he gets verified automatically

The codes will only be saved in memory since this is a quick process and it doesn't make sense to save them between restarts.

It will also verify that user on any other server with the Bot where the student is.

### Verify automatically

User joins guild callback, not a command

If a student joins a server with the bot, and that student is already verified on another server with the same bot, the user automatically get verified.

### Ping

Type: Slash command, Prefix command

Permission: everyone

Ping Command

### TMPC Commands

Type: Prefix command

Permission: Owner of the tmpc channel where the command is done, Moderator

Following commands need to be available:

* keep
* release
* hide
* show
* lock
* unlock
* rename
* token [gen|show]
* kick
* delete

### TMPC token place

Type: Prefix command

Permission: Owner of a tmpc channel

The command will ask the user what tmpc to put the invite of via an Interaction. The user can then select from all tmpc that the user owns.

There also need to be a reaction added callback that checks when the join emoji is clicked by a user.

### TMPC no mod

Type: Prefix command

Permission: Moderator

The command will keep Moderator out of the tmpc where the command is done.

### TMPC leave

Type: Prefix command

Permission: User that has joined a tmpc in the past

Remove the user from the permission list, making him as if he never joined. He can join again if the channel if unlocked.

### TMPC join channel add

Type: Prefix command

Permission: Guild admin

Adds a new "Join Here" voice channel to the list of tmpc creator channels. The command will take in a pattern and if the channels are allowed to be made persistent.

### TMPC join channel remove

Type: Prefix command

Permission: Guild admin

Removed a registered "Join Here" channel.

### TMPC remove old channels

loop, not a command

Every X Minutes, check if there are any channels that should be deleted. This is necessary so that channels that got empty while the bot was not online, are eventually deleted.

### TMPC set permission

User joins/leaves voice chat callback, not a command

When a user joins a tmpc voice channel, set the permissions of the voice channel and the text channel so that the user can see and join the channels even if they are locked and hidden in the future.

Also if the tmpc channel is now empty, try to delete the tmpc if it is necessary.

### Link add

Type: Prefix command

Permission: Guild admin

Adds a links between a study group and a subject.

### Link remove

Type: Prefix command

Permission: Guild admin

Removes a links between a study group and a subject.

### Link show

Type: Prefix command

Permission: Guild admin

Shows all links between study groups and subjects.

### Grace Period

User joins guild callback, not a command

If a user joins the guild and a tmp student role is known, add that role to the student.

### NSFW / Newsletter Add / Remove

Type: Slash command, Prefix command

Permission: Verified user

A verified user can add/remove himself from the newsletter/nsfw role

### Subject show

Type: Slash command, Prefix command

Permission: Verified user

Print a list of subject to the user that he can add / remove from himself

### Subject add / rm

Type: Slash command, Prefix command

Permission: Verified user

Add / Remove a subject role from the user.

### Add new subject

Type: Prefix command

Permission: Guild admin

Creates a new subject role and chat

### Remove subject

Type: Prefix command

Permission: Guild admin

Deletes a subject role and chat

### List subjects without link

Type: Prefix command

Permission: Guild admin

List all subjects that don't have a link to any study group. This is used to see old, dangling subjects.

## Removed commands from the python version

Renamed commands are not considered removed

### Replaced by setup command

* `group [category|separator]`
* `kick [*]`
* `safeRoles [add|rm|rm]`
* `mail`
* `man`
* `subjects [category|separator]`

### Others

* `cog [load|reload|unload]` : replaced by individual en/disable command
* `purge [chat|member]` : no need, is replaced by the raid, spam help of Discord
* `toggle <command>` : replaced by individual en/disable command
* `logger` : logger level can't be set anymore
* `mail` : removed since never used
* `man` : removed since never used
* `list-guild-member` : removed since never used
* `tmpc [join|invite]` : removed since never used
* `mongo [*]` : removed since we won't use mongo
* `nerd voice` : removed to clean up features
