from discord import Embed,Interaction,Role
from . import error_response

MAX_SPACING: int = 26

def embed(interaction: Interaction,description: str,role_a: Role,label_a: str,role_b: Role,label_b: str) -> Embed:
    assert interaction.guild
    hierarchy: str = ""
    spacing_amount: int = min(MAX_SPACING,max(len(role.name)+1 for role in interaction.guild.roles))
    for role in interaction.guild.roles[::-1]:
        spacing: str = role.name.ljust(spacing_amount,' ').split(role.name)[1]
        hierarchy += f"\n{role.mention}{spacing}"
        if role == role_a or role == role_b:
            hierarchy += "     ⬅️     **"
            if role_a == role_b:
                hierarchy += f"{label_a} & {label_b}"
            elif role == role_a:
                hierarchy += label_a
            else:
                hierarchy += label_b
            hierarchy += "**"
    return error_response.embed(interaction,f"{description}\n{hierarchy}")