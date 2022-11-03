# pyright: reportUnusedFunction=false

import asyncio
from discord import Embed,Guild,Interaction,Invite,Member,Permissions
from discord.abc import GuildChannel
from discord.app_commands import Choice,CommandTree,describe,guild_only,default_permissions
from modubot import ModuleBase
from typing import List,Optional,TYPE_CHECKING

from ..responses import *
if TYPE_CHECKING:
    from modubot import Bot
    from ..persistence_layer import Module as PersistenceLayer
    from ...core.slash_commands import Module as SlashCommands

class Module(ModuleBase):
    def __init__(self,bot: 'Bot'):
        self._bot: Bot = bot
    
    async def postinit(self):
        persistence_layer: PersistenceLayer = self._bot.get_module("modules.invite_role_bot.persistence_layer")
        slash_commands: SlashCommands = self._bot.get_module("modules.core.slash_commands")
        cmd_tree: CommandTree[Bot] = slash_commands.cmd_tree

        @guild_only()
        @default_permissions(manage_guild=True,manage_roles=True)
        @cmd_tree.command(name="invclone",description="Clones an invite but with a different URL.")
        @describe(invite_url="The URL of the invite to clone.")
        async def invclone(interaction: Interaction,invite_url: str):
            assert interaction.guild
            assert isinstance(interaction.user,Member)
            bot_guild_permissions: Permissions = interaction.guild.me.guild_permissions
            response_embed: Embed
            await interaction.response.defer(ephemeral=True,thinking=True)
            invite_code: str = invite_url.split('/')[-1]
            invites: List[Invite] = [invite for invite in await interaction.guild.invites() if invite.code == invite_code]  #In order to see invite attributes
            invite: Optional[Invite] = invites[0] if invites else None
            if not invite:
                response_embed = invalid_invite_response.embed(interaction,invite_url)
            elif not bot_guild_permissions.create_instant_invite:
                response_embed = create_instant_invite_response.embed(interaction)
            elif not isinstance(invite.channel,GuildChannel):
                response_embed = wrong_guild_response.embed(interaction,invite_url)
            else:
                cloned_invite: Invite = await invite.channel.create_invite(
                    max_age=invite.max_age or 0,
                    max_uses=invite.max_uses or 0,
                    temporary=invite.temporary or False,
                    unique=True,
                    reason=f"Cloned invite '{invite.url}'",
                    target_type=invite.target_type,
                    target_user=invite.target_user,
                    target_application_id=invite.target_application.id if invite.target_application else None
                )
                response_embed = cloned_response.embed(interaction,cloned_invite.url)
            await interaction.followup.send(embed=response_embed,ephemeral=True)
        
        async def get_all_guild_invites(guild: Guild) -> List[Invite]:
            invites: List[Invite] = []
            invites += await persistence_layer.get_cached_guild_invites(guild)
            return invites

        @invclone.autocomplete("invite_url")
        async def invclone_auto_invite_url(interaction: Interaction,current: str) -> List[Choice[str]]:
            guild: Optional[Guild] = interaction.guild
            if guild:
                try:
                    invites: List[Invite] = await asyncio.wait_for(get_all_guild_invites(guild),timeout=2)
                    return [Choice(name=invite.url,value=invite.url) for invite in invites if current.lower().strip() in invite.url.lower()][:25]
                except asyncio.TimeoutError:
                    pass
            return [Choice(name="Unable to load invites, please try again later.",value="lol_dont_actually_click_me")]