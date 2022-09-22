# pyright: reportUnusedFunction=false

from discord import Embed,Interaction
from discord.app_commands import CommandTree,guild_only
from discord.ui import View
from modubot import ModuleBase
from typing import TYPE_CHECKING
from ..invite_role_bot_config import InviteRoleBotConfig

from ..responses import *
if TYPE_CHECKING:
    from modubot import Bot
    from ...core.slash_commands import Module as SlashCommands

class Module(ModuleBase):
    def __init__(self,bot: 'Bot'):
        self.bot: Bot = bot
        self.config: InviteRoleBotConfig = self.bot.config.get(InviteRoleBotConfig)
    
    async def postinit(self):
        slash_commands: SlashCommands = self.bot.get_module("modules.core.slash_commands")
        cmd_tree: CommandTree[Bot] = slash_commands.cmd_tree
        
        @guild_only()
        @cmd_tree.command(name="help",description=f"Learn more about {self.bot.user.display_name if self.bot.user else 'Invite-Role Bot'}.")
        async def help(interaction: Interaction):
            response_embed: Embed
            response_view: View
            await interaction.response.defer(ephemeral=True,thinking=True)
            response_embed,response_view = help_response.embed(interaction,self.config.help_command)
            await interaction.followup.send(embed=response_embed,view=response_view,ephemeral=True)