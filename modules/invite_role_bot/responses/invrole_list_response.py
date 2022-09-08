from discord import Color,Embed,Interaction,Invite,Member,Permissions,Role
from discord.abc import GuildChannel
from typing import Dict,List,Tuple
from . import base_response
from .pagination_view import PaginationView

def embed(interaction: Interaction,invite_roles_raw: Dict[Invite,List[Role]]) -> Tuple[Embed,PaginationView]:
    assert interaction.guild
    assert isinstance(interaction.user,Member)
    embed: Embed = base_response.embed(interaction)
    embed.color = Color.blue()
    embed.title = f"Invite-Roles for {interaction.guild.name}:"
    embed.description = "*Note: Certain invite URLs may be hidden above because they assign roles with permissions that are higher than yours.*"
    pagination_view: PaginationView = PaginationView(embed=embed)

    if invite_roles_raw:
        member_permissions: Permissions = interaction.user.guild_permissions
        for invite,roles in invite_roles_raw.items():
            role_permissions: Permissions = Permissions()
            for role in roles:
                role_permissions |= role.permissions
            pagination_view.add_field(
                name = "‍",
                value = f"""
                **Invite URL:** {invite.url if role_permissions <= member_permissions else "*Hidden*"}
                **Channel:** {invite.channel.mention if isinstance(invite.channel,GuildChannel) else "*Unknown*"}
                **Roles:** {", ".join([role.mention for role in roles])}
                """,
                inline = False
            )
    else:
        pagination_view.add_field(
                name = "‍",
                value = """
                **⚠️No invite-roles are currently connected!⚠️**
                Use `/invrole connect` to get started!
                """,
                inline = False
            )
    return (embed,pagination_view)