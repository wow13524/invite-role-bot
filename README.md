# Invite-Role Bot

A bot that assigns roles to new guild members depending on the invite URL used to join, written in Python using [Modubot](https://github.com/wow13524/discord-modubot).

---

## Commands
> ### `/help`
> Shows a help menu containing the command list and some useful links.
> 
> ### `/invrole connect [invite_url: str] [role: Role]`
> Connects any invite URL from the guild to any role.  One invite URL can have multiple roles connected.
> 
> ### `/invrole disconnect [invite_url: str] <role: Role>`
> Disconnects one or all roles from the specified invite URL.  If a role is given, only that role is disconnected from the invite URL; otherwise, every role associated with the given invite URL will be disconnected.
> 
> ### `/invrole list`
> Shows a list of all invite-role connections within this guild.

## Getting Started
*Note: The bot application used should have the **Server Members Intent** enabled through the Discord developers dashboard.*

Clone the repository, populate `BotConfig.token` in the provided `config.json`, and run `main.py`.

The bot should connect to Discord and function with no further configuration needed.

## TODO
- Reaction roles (submodule)
- Redundant worker threads to mitigate dropped events