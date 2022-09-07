from discord import Embed,Interaction,Role
from . import success_response

def embed(interaction: Interaction,invite_url: str,role: Role) -> Embed:
    return success_response.embed(interaction,f"The invite **{invite_url}** is now connected to {role.mention}.")