from discord import Embed,Interaction,Member,Role
from . import role_hierarchy_response

def embed(interaction: Interaction,target_role: Role) -> Embed:
    assert interaction.guild
    assert isinstance(interaction.user,Member)
    return role_hierarchy_response.embed(
        interaction=interaction,
        description="""
        You don't have permission to assign that role to other users!\n
        In order to do so, **Your Role** must be placed above the **Target Role** in the guild role hierarchy.
        """,
        role_a=interaction.user.top_role,
        label_a="Your Role",
        role_b=target_role,
        label_b="Target Role"
    )