This is my desing of a multicog bot.

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

## Current cogs
- `core_cogs/pingcog.py` - a simple cog that has a ping command to check the bot latency.
- `core_cogs/controll_cog.py` - a cog that has commands to control the bot (`/reload cogs`, `/restart`, `/shutdown`).

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

You can use the decorators `@events.on_event(event_name, another_event_name, ...)` to add an event listener for specific events. The event listener will be called when any of the specified events are triggered by `events.call(event_name)`

If a function is a loop/long lasting async task, I recommend adding `close_on_shutdown=True` to the `@events.on_event`. This will cancel the task on bot shutdown.

# Roles Channels ect IDs
All of the IDs are stored in `config.py` with the class `IDs`.

`IDs` uses a nested class system to organize the IDs, for example `IDs.CHANNELS.CONSOLE_LOGS` is the ID of the channel where the bot logs the console.

The class is also compiled into a `IDsObjects` class that returns the discord objects instead of the IDs.
Example use; `ids_objects.CHANNELS.CONSOLE_LOGS.send("hello")`
