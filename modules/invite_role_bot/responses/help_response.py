from discord import ButtonStyle,Color,Embed,Interaction
from discord.ui import Button,View
from typing import Tuple
from . import base_response
from ..invite_role_bot_config import HelpConfig


class HelpView(View):
    def __init__(self,*,timeout: float=180.0,config: HelpConfig) -> None:
        super().__init__(timeout=timeout)
        self.add_item(Button(style=ButtonStyle.primary,label="Invite",url=config.invite_url,emoji="🔗"))
        self.add_item(Button(style=ButtonStyle.primary,label="GitHub",url=config.github_url,emoji="💻"))
        self.add_item(Button(style=ButtonStyle.primary,label="Privacy Policy",url=config.privacy_policy_url,emoji="📃"))
        self.add_item(Button(style=ButtonStyle.green,label="Donate",url=config.donate_url,emoji="💸"))

def embed(interaction: Interaction,config: HelpConfig) -> Tuple[Embed,HelpView]:
    assert interaction.guild
    embed: Embed = base_response.embed(interaction)
    embed.color = Color.blue()
    embed.title = f"Hello, I'm {interaction.guild.me.display_name}!"
    embed.description = f"""
    **{interaction.guild.me.display_name}** is a guild utility bot which can automatically assign roles to new guild members depending on the invite URL used to join.
    The command list can be found by typing `/` in chat or below:
    """
    embed.add_field(name="/help",value="Shows a help menu containing the command list and some useful links.",inline=False)
    embed.add_field(name="/invrole connect",value="Connects any invite URL from this guild to any role.",inline=False)
    embed.add_field(name="/invrole disconnect",value="Disconnects one or all roles from the specified invite URL.",inline=False)
    embed.add_field(name="/invrole list",value="Shows a list of all invite-role connections within this guild.",inline=False)
    help_view: HelpView = HelpView(config=config)
    return (embed,help_view)