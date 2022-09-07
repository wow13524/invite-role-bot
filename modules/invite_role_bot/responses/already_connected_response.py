from discord import Embed,Interaction,Role
from . import error_response

def embed(interaction: Interaction,invite_url: str,role: Role) -> Embed:
    return error_response.embed(interaction,f"The invite **{invite_url}** is already connected to {role.mention}.")