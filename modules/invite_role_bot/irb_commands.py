# pyright: reportUnusedFunction=false

from discord import Interaction,Invite,Role
from discord.app_commands import CommandTree
from discord.errors import NotFound
from modubot import ModuleBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modubot import Bot
    from .irb_data_persistence import Module as DataPersistence
    from ..core.slash_commands import Module as SlashCommands

class Module(ModuleBase):
    name = "irb_commands"

    def __init__(self,bot: 'Bot'):
        self.bot: Bot = bot
    
    async def postinit(self):
        data_persistence: DataPersistence = self.bot.get_module("irb_data_persistence")
        slash_commands: SlashCommands = self.bot.get_module("slash_commands")
        cmd_tree: CommandTree[Bot] = slash_commands.cmd_tree

        @cmd_tree.command(name="connect",description="test connect command!")
        async def connect(interaction: Interaction,invite_url: str,role: Role):
            try:
                invite: Invite = await self.bot.fetch_invite(invite_url)
            except NotFound:
                await interaction.response.send_message("Invite not found.")
            else:
                await data_persistence.add_invite_role(invite,role)
                await interaction.response.send_message("connected!")