from discord import Color,Embed,Interaction,Invite,Member,Permissions,Role
from discord.abc import GuildChannel
from typing import Dict,List,Optional,Tuple,TypedDict
from . import base_response
from .pagination_view import PaginationView

class RolesPair(TypedDict):
    active_roles: List[Role]
    inactive_roles: List[Role]

def format_roles_pair(roles_pair: RolesPair) -> str:
    active_roles: str = ", ".join([role.mention for role in roles_pair["active_roles"]])
    inactive_roles: str = ", ".join([f"~~{role.mention}~~" for role in roles_pair["inactive_roles"]])
    return f"{active_roles}{', ' if active_roles and inactive_roles else ''}{inactive_roles}"

def embed(interaction: Interaction,invite_roles_raw: Dict[str,RolesPair],guild_invites: List[Invite]) -> Tuple[Embed,PaginationView]:
    assert interaction.guild
    assert isinstance(interaction.user,Member)
    embed: Embed = base_response.embed(interaction)
    embed.color = Color.blue()
    embed.title = f"Invite-Roles for {interaction.guild.name}:"
    embed.description = """
    *Note: Certain invite URLs may be hidden below because they assign roles with permissions that are higher than yours.
    
    ~~Crossed out~~ roles are connected but will not be assigned to new members because I don't have permission to assign them.*
    """
    pagination_view: PaginationView = PaginationView(embed=embed)

    if invite_roles_raw:
        guild_invites_dict: Dict[str,Invite] = {invite.code:invite for invite in guild_invites}
        member_permissions: Permissions = interaction.user.guild_permissions
        for invite_code,roles_pair in invite_roles_raw.items():
            linked_invite: Optional[Invite] = guild_invites_dict[invite_code] if invite_code in guild_invites_dict else None
            role_permissions: Permissions = Permissions()
            for role in roles_pair["active_roles"]:
                role_permissions |= role.permissions
            for role in roles_pair["inactive_roles"]:
                role_permissions |= role.permissions
            pagination_view.add_field(
                name = "‍",
                value = f"""
                **Invite URL:** {f"https://discord.gg/{invite_code}" if role_permissions <= member_permissions else "*Hidden*"}{" (*expired*)" if not linked_invite else ""}
                **Channel:** {linked_invite.channel.mention if linked_invite and isinstance(linked_invite.channel,GuildChannel) else "*Unknown*"}
                **Roles:** {format_roles_pair(roles_pair)}
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