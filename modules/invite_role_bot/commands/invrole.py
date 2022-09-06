# pyright: reportUnusedFunction=false

from discord import Guild,Interaction,Invite,Member,Permissions,Role
from discord.app_commands import Choice,CommandTree,describe,Group
from discord.errors import NotFound
from modubot import ModuleBase
from typing import List,Optional,TYPE_CHECKING
from ..responses import *
if TYPE_CHECKING:
    from modubot import Bot
    from ..persistence_layer import Module as PersistenceLayer
    from ...core.slash_commands import Module as SlashCommands

class Module(ModuleBase):
    def __init__(self,bot: 'Bot'):
        self.bot: Bot = bot
    
    async def postinit(self):
        persistence_layer: PersistenceLayer = self.bot.get_module("modules.invite_role_bot.persistence_layer")
        slash_commands: SlashCommands = self.bot.get_module("modules.core.slash_commands")
        cmd_tree: CommandTree[Bot] = slash_commands.cmd_tree

        invrole_group: Group = Group(name="invrole",description="Manage invite-role connections within this guild.",guild_only=True,default_permissions=Permissions(manage_guild=True,manage_roles=True))
        
        @invrole_group.command(name="connect",description="Connects an invite to a role.")
        @describe(invite_url="The URL of the invite to link a role to.",role="The role to assign when the invite is used.")
        async def connect(interaction: Interaction,invite_url: str,role: Role):
            assert interaction.guild
            assert isinstance(interaction.user,Member)
            try:
                invite: Invite = await self.bot.fetch_invite(invite_url)
            except NotFound:
                await interaction.response.send_message(embed=error_response.embed(interaction,"Invite not found."))
            else:
                if invite.guild != interaction.guild:
                    await interaction.response.send_message(embed=error_response.embed(interaction,"Invite does not belong to this guild."))
                elif not interaction.guild.me.guild_permissions.manage_guild:
                    await interaction.response.send_message(embed=error_response.embed(interaction,"I don't have permission to assign roles."))
                elif interaction.user != interaction.guild.owner and interaction.user.top_role <= role:
                    await interaction.response.send_message(embed=error_response.embed(interaction,"You do not have permission to assign this role."))
                elif role.position == 0 or interaction.guild.me.top_role <= role:
                    await interaction.response.send_message(embed=error_response.embed(interaction,"I'm unable to assign this role."))
                elif await persistence_layer.invite_role_exists(invite,role):
                    await interaction.response.send_message(embed=error_response.embed(interaction,"This invite and role are already connected."))
                else:
                    await persistence_layer.add_invite_role(invite,role)
                    await interaction.response.send_message(embed=success_response.embed(interaction,"Connected!"))
        
        @connect.autocomplete("invite_url")
        async def connect_auto_invite_url(interaction: Interaction,current: str) -> List[Choice[str]]:
            guild: Optional[Guild] = interaction.guild
            invites: List[Invite] = []
            if guild:
                invites = await guild.invites()
            return [Choice(name=invite_url,value=invite_url) for invite_url in map(lambda x: f"https://discord.gg/{x.code}",invites) if current.lower() in invite_url.lower()]
        
        @invrole_group.command(name="disconnect",description="Disconnects an invite from a role.")
        @describe(invite_url="The URL of the invite to disconnect a role from.",role="The role to disconnect from the invite.")
        async def disconnect(interaction: Interaction,invite_url: str,role: Optional[Role]):
            try:
                invite: Invite = await self.bot.fetch_invite(invite_url)
            except NotFound:
                await interaction.response.send_message(embed=error_response.embed(interaction,"Invite not found."))
            else:
                if not await persistence_layer.invite_role_exists(invite,role):
                    await interaction.response.send_message(embed=error_response.embed(interaction,"No connection exists."))
                else:
                    await persistence_layer.remove_invite_role(invite,role)
                    await interaction.response.send_message(embed=success_response.embed(interaction,"Disconnected!"))
        
        @disconnect.autocomplete("invite_url")
        async def disconnect_auto_invite_url(interaction: Interaction,current: str) -> List[Choice[str]]:
            guild: Optional[Guild] = interaction.guild
            invites: List[str] = []
            if guild:
                invites = await persistence_layer.get_invite_codes(guild)
            return [Choice(name=invite_url,value=invite_url) for invite_url in map(lambda x: f"https://discord.gg/{x}",invites) if current.lower() in invite_url.lower()]

        @invrole_group.command(name="list",description="Lists all invite-role connections.")
        async def list(interaction: Interaction):
            assert interaction.guild
            invites: List[Invite] = await persistence_layer.get_invites(interaction.guild)
            response: str = ""
            for invite in invites:
                invite_roles: List[Role] = await persistence_layer.get_invite_roles(invite)
                response += f"<https://discord.gg/{invite.code}>: {' '.join(role.mention for role in invite_roles)}\n"
            await interaction.response.send_message(response or "No invite-roles connected.")
        
        cmd_tree.add_command(invrole_group)