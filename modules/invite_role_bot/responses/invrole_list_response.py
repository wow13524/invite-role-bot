from discord import Color,Embed,Interaction,Invite,Member,Permissions,Role
from discord.abc import GuildChannel
from typing import Dict,List,Optional,Tuple
from . import base_response
from .pagination_view import PaginationView

def embed(interaction: Interaction,invite_roles_raw: Dict[str,List[Role]],guild_invites: List[Invite]) -> Tuple[Embed,PaginationView]:
    assert interaction.guild
    assert isinstance(interaction.user,Member)
    embed: Embed = base_response.embed(interaction)
    embed.color = Color.blue()
    embed.title = f"Invite-Roles for {interaction.guild.name}:"
    embed.description = "*Note: Certain invite URLs may be hidden above because they assign roles with permissions that are higher than yours.*"
    pagination_view: PaginationView = PaginationView(embed=embed)

    if invite_roles_raw:
        guild_invites_dict: Dict[str,Invite] = {invite.code:invite for invite in guild_invites}
        member_permissions: Permissions = interaction.user.guild_permissions
        for invite_code,roles in invite_roles_raw.items():
            linked_invite: Optional[Invite] = guild_invites_dict[invite_code] if invite_code in guild_invites_dict else None
            role_permissions: Permissions = Permissions()
            for role in roles:
                role_permissions |= role.permissions
            pagination_view.add_field(
                name = "‍",
                value = f"""
                **Invite URL:** {f"https://discord.gg/{invite_code}" if role_permissions <= member_permissions else "*Hidden*"}{" (*expired*)" if not linked_invite else ""}
                **Channel:** {linked_invite.channel.mention if linked_invite and isinstance(linked_invite.channel,GuildChannel) else "*Unknown*"}
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