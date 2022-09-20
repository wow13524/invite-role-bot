from discord import Embed,Interaction,Role
from . import error_response

MAX_SPACING: int = 32
ROLE_OVERFLOW: int = 2

def embed(interaction: Interaction,description: str,role_a: Role,label_a: str,role_b: Role,label_b: str) -> Embed:
    assert interaction.guild
    hierarchy: str = ""
    spacing_amount: int = min(MAX_SPACING,max(len(role.name)+1 for role in interaction.guild.roles))
    index_a: int = interaction.guild.roles.index(role_a)
    index_b: int = interaction.guild.roles.index(role_b)
    gap_state_curr: int = -1
    gap_state_next: int = 0
    for i,role in enumerate(interaction.guild.roles):
        if i in range(index_a-ROLE_OVERFLOW,index_a+ROLE_OVERFLOW+1) or i in range(index_b-ROLE_OVERFLOW,index_b+ROLE_OVERFLOW+1):
            spacing: str = role.name.ljust(spacing_amount,' ').split(role.name)[1]
            line: str = f"{role.mention}{spacing}"
            if role == role_a or role == role_b:
                gap_state_next += 1
                line += "     ⬅️     **"
                if role_a == role_b:
                    line += f"{label_a}/{label_b}"
                elif role == role_a:
                    line += label_a
                else:
                    line += label_b
                line += "**"
            hierarchy = f"\n{line}"+hierarchy
        elif gap_state_curr != gap_state_next:
            gap_state_curr = gap_state_next
            hierarchy = f"\n**.   .   .   .   .**"+hierarchy
    return error_response.embed(interaction,f"{description}\n{hierarchy}")