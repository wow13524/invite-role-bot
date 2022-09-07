from discord import Embed,Interaction,Role
from . import role_hierarchy_response

def embed(interaction: Interaction,target_role: Role) -> Embed:
    assert interaction.guild
    return role_hierarchy_response.embed(
        interaction=interaction,
        description="""
        I don't have permission to assign that role to other users!\n
        In order to do so, **My Role** must be placed above the **Target Role** in the guild role hierarchy.
        """,
        role_a=interaction.guild.me.top_role,
        label_a="My Role",
        role_b=target_role,
        label_b="Target Role"
    )