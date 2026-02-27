This is how I (@loleczkowo) desing discord bot's.
If you want fell free to contact me i can make a bot for you OR explain how this piece of spaghetti works

This is a template, so you can easily add your own cogs and commands. You can also modify the existing cogs and commands to fit your needs.  
Feel free to use this code. I appreciate if you give me credit, but you dont have to :D.

Currently its configured for me, but you can easily change the configuration in `config.py` file.

The bot is only for single-server use, but you can easily modify it to work on multiple servers if you want to.  
(to modify the bot you will have to rewrite the log system, because currently it is designed for single-server use)

This project was written with minimal help from AI because fuck AI.

# The cog system
The bot is designed to be modular, so you can easily add and remove cogs. Each cog is a separate file in the `cogs` folder, and you can load them in the `cogs/__init__.py` file.

## Adding a cog
1. Create a new file in the `cogs` *(or `cogs/anysubfolder`)*, for example `mycog.py`.
2. Create a new class in the file that inherits from `commands.Cog`, for example `class MyCog(commands.Cog):`.
3. Add an `__init__` method to the class that takes a `commands.Bot`
4. Add your commands to the class using the `@commands.command()` and `@app_commands.command()` decorators.
5. Load the cog in the `cogs/__init__.py` by adding it to the `cog_list` list.
The example of a cog can be found in `cogs/core_cogs/pingcog.py` file. You can also check the existing cogs for reference.
6. Use the bot's `/_sync_commands` command and reload your discord client with `CTRL+R`

## Current cogs
Main cogs;
- `core_cogs/controll_cog.py` - a cog that has commands to control the bot (`/_reload cogs`, `/_sync commands`, `/_restart`, `/_shutdown`, `/_botstatus`).
- `core_cogs/helpcog.py` - basic `help` command.
More optional cogs;
- `buildin_cogs/pingcog.py` - a simple cog that has a ping command to check the bot latency.
- `buildin_cogs/rolescog.py` - allows user to make role selections.
- `buildin_cogs/starboard.py` - complex starboard module.

# Error handling
The bot has a built-in error handling system that catches common errors and sends a message to the user. The error handling is done in the `core/handle_command_error.py` file.  
You can modify the error handling to fit your needs, or add more specific error handling for your commands with the help of `core/check_permission.py`.

# Logging
The bot uses a custom logging system `core/log.py`. It logs important events and errors to a specific channel in the server, and also prints them to the console and writes them to a log file.

The formatting is quite bad. Feel free to rewrite the logging system.

The list of log levels is stored in `config.py` file, you can easily add more log levels or modify the existing ones.
The log levels are used to determine where the log should be sent (console, file, discord) and if it should ping a specific role.

In code you can also overwrite the log levels for specific logs, for example you can make a log that is only visible in the channel and not in the console or log file, or a log that pings a specific role.
An example of a log;
> log(INFO(to_discord=True, to_file=False, to_console=False, ping=True), "Bot has started successfully!")

# Event handling
The bot has a build-in event handling system that allows you to easily add event listeners. The event handling is done in the `core/handle_events.py` file.

The list of Events is stored in `config.py` file, you can easily add more events.

You can use the decorators `@events.on_event(event_name, another_event_name, ...)` *(`cog_on_event` for cogs)* to add an event listener for specific events. The event listener will be called when any of the specified events are triggered by `events.call(event_name)`  
You can also use `events.register(func, event_name, another_event_name, ...)` to register a function without using a decorator.  
To unregister an event listener, you can use `events.unregister(func)`. *(works for both decorator and register)*

If a function is a loop/long lasting async task, I recommend adding `close_on_shutdown=True` to the `@events.on_event`. This will cancel the task on bot shutdown.

# Roles Channels ect IDs
All of the IDs are stored in `config.py` with the class `IDs`.

`IDs` uses a nested class system to organize the IDs, for example `IDs.CHANNELS.CONSOLE_LOGS` is the ID of the channel where the bot logs the console.

The class is also compiled into a `IDsObjects` class that returns the discord objects instead of the IDs.
Example use; `ids_objects.CHANNELS.CONSOLE_LOGS.send("hello")`

# Memory
To store varibles that keep their value after bot restart, you can use the `Memory` class from `core/memory.py`.  
Defining a varible goes like `varible123 = Memory("varible123", default=0,)`, To get it use `varible123.mem`.  
The varible will save itself to a file `memory/memory.json` or `memory/cogs/Cmemory_CogName.json`. As it is a json it can only support normal data  
Data will save every `MEMORY_AUTOSAVE_TIME` seconds. If you need the data to be saved immediately after change, you can add `save_on_change=True`.

# Categories
Discord uses already has "command categories" But it uses cogs. This bot has a more of Command-Per-Cog system.
Therefore Ive implemented a custom category system in `core/command_category`  
When adding a command you can use `@categories.set_category(CT_ADMIN)` to set a command's category. You can also use `@categories.set_cog_category(CT_BOT_OWNER)` to set a default category for a cog.  
List of categories is stored in `config.py` file, similary to Events.
The current category system is only for the `help` command to categorise commands.
