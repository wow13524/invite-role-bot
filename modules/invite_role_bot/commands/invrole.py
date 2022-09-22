# pyright: reportUnusedFunction=false

from discord import Embed,Guild,Interaction,Invite,Member,Permissions,Role
from discord.app_commands import Choice,CommandTree,describe,Group
from discord.errors import NotFound
from discord.ui import View
from modubot import ModuleBase
from typing import Dict,List,Optional,TYPE_CHECKING

from ..responses import *
if TYPE_CHECKING:
    from modubot import Bot
    from ..persistence_layer import Module as PersistenceLayer
    from ...core.slash_commands import Module as SlashCommands

def permission_check(embed: Embed,permissions: Permissions) -> None:
    if not (permissions.manage_guild and permissions.manage_roles):
        missing_permissions: List[str] = []
        if not permissions.manage_guild:
            missing_permissions.append("**Manage Server**")
        if not permissions.manage_roles:
            missing_permissions.append("**Manage Roles**")
        embed.description = f"🚨IMPORTANT🚨: I'm currently unable to track or assign invite-roles because I don't have the {' and '.join(missing_permissions)} permission{'s' if len(missing_permissions) > 1 else ''}!\n\n" + (embed.description or "")

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
            bot_guild_permissions: Permissions = interaction.guild.me.guild_permissions
            response_embed: Embed
            await interaction.response.defer(ephemeral=True,thinking=True)
            try:
                invite_url = f"https://discord.gg/{invite_url.split('/')[-1]}"
                invite: Invite = await self.bot.fetch_invite(invite_url)
            except NotFound:
                response_embed = invalid_invite_response.embed(interaction,invite_url)
            else:
                if invite.guild != interaction.guild:
                    response_embed = wrong_guild_response.embed(interaction,invite_url)
                elif not bot_guild_permissions.manage_roles:
                    response_embed = manage_roles_response.embed(interaction)
                elif interaction.user.id != interaction.guild.owner_id and interaction.user.top_role <= role:
                    response_embed = invoker_hierarchy_response.embed(interaction,role)
                elif role.position == 0 or role.is_bot_managed():
                    response_embed = cannot_assign_response.embed(interaction,role)
                elif interaction.guild.me.top_role <= role:
                    response_embed = bot_hierarchy_response.embed(interaction,role)
                elif await persistence_layer.invite_role_exists(invite,role):
                    response_embed = already_connected_response.embed(interaction,invite_url,role)
                else:
                    await persistence_layer.add_invite_role(invite,role)
                    response_embed = connected_response.embed(interaction,invite_url,role)
            permission_check(response_embed,bot_guild_permissions)
            await interaction.followup.send(embed=response_embed,ephemeral=True)
        
        @connect.autocomplete("invite_url")
        async def connect_auto_invite_url(interaction: Interaction,current: str) -> List[Choice[str]]:
            guild: Optional[Guild] = interaction.guild
            invites: List[Invite] = []
            if guild and guild.me.guild_permissions.manage_guild:
                if guild.vanity_url_code:
                    vanity_invite: Optional[Invite] = await guild.vanity_invite()
                    if vanity_invite:
                        invites.append(vanity_invite)
                invites += await guild.invites()
            return [Choice(name=invite.url,value=invite.code) for invite in invites if current.lower().strip() in invite.url.lower()][:25]
        
        @invrole_group.command(name="disconnect",description="Disconnects an invite from a role.")
        @describe(invite_url="The URL of the invite to disconnect a role from.",role="The role to disconnect from the invite.")
        async def disconnect(interaction: Interaction,invite_url: str,role: Optional[Role]):
            assert interaction.guild
            response_embed: Embed
            response_view: Optional[View] = None
            await interaction.response.defer(ephemeral=True,thinking=True)
            try:
                invite_url = f"https://discord.gg/{invite_url.split('/')[-1]}"
                invite: Invite = await self.bot.fetch_invite(invite_url)
            except NotFound:
                response_embed = invalid_invite_response.embed(interaction,invite_url)
            else:
                if not await persistence_layer.invite_role_exists(invite,role):
                    response_embed = not_connected_response.embed(interaction,invite_url,role)
                else:
                    async def remove_invite_role(interaction: Interaction) -> Embed:
                        await persistence_layer.remove_invite_role(invite,role)
                        return disconnected_response.embed(interaction,invite_url,role)
                    if role:
                        response_embed = await remove_invite_role(interaction)
                    else:
                        active_roles: List[Role]
                        active_roles,inactive_roles = await persistence_layer.get_invite_roles(interaction.guild,invite.code)
                        response_embed,response_view = disconnect_confirm_response.embed(
                            interaction,
                            invite_url,
                            len(active_roles)+len(inactive_roles),
                            remove_invite_role
                        )
            permission_check(response_embed,interaction.guild.me.guild_permissions)
            if response_view:
                await interaction.followup.send(embed=response_embed,view=response_view,ephemeral=True)
            else:
                await interaction.followup.send(embed=response_embed,ephemeral=True)
        
        @disconnect.autocomplete("invite_url")
        async def disconnect_auto_invite_url(interaction: Interaction,current: str) -> List[Choice[str]]:
            guild: Optional[Guild] = interaction.guild
            invites_codes: List[str] = []
            if guild:
                invites_codes = await persistence_layer.get_invite_codes(guild)
            return [Choice(name=f"https://discord.gg/{invite_code}",value=invite_code) for invite_code in invites_codes if current.lower().strip() in f"https://discord.gg/{invite_code}".lower()][:25]

        @invrole_group.command(name="list",description="Lists all invite-role connections.")
        async def list(interaction: Interaction):
            assert interaction.guild
            response_embed: Embed
            response_view: Optional[View]
            invite_roles_raw: Dict[str,invrole_list_response.RolesPair] = {}
            await interaction.response.defer(ephemeral=True,thinking=True)
            for invite_code in await persistence_layer.get_invite_codes(interaction.guild):
                active_roles: List[Role]
                inactive_roles: List[Role]
                active_roles,inactive_roles = await persistence_layer.get_invite_roles(interaction.guild,invite_code)
                invite_roles_raw[invite_code] = {
                    "active_roles": active_roles,
                    "inactive_roles": inactive_roles
                }
            guild_invites: List[Invite] = await persistence_layer.get_invites(interaction.guild)
            response_embed,response_view = invrole_list_response.embed(interaction,invite_roles_raw,guild_invites)
            permission_check(response_embed,interaction.guild.me.guild_permissions)
            await interaction.followup.send(embed=response_embed,view=response_view,ephemeral=True)
        
        cmd_tree.add_command(invrole_group)