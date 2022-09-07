from discord import Embed,Interaction,Role
from . import error_response

def embed(interaction: Interaction,description: str,role_a: Role,label_a: str,role_b: Role,label_b: str) -> Embed:
    assert interaction.guild
    hierarchy: str = ""
    for role in interaction.guild.roles:
        hierarchy += f"\n{role.mention}{' **<- ' if role == role_a or role_b else ''}{label_a+' **' if role == role_a else ''}{label_b+' **' if role == role_b else ''}"
    return error_response.embed(interaction,f"{description}\n{hierarchy}")