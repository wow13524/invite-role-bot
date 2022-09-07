from discord import Embed,Interaction,Role
from typing import Optional
from . import error_response

def embed(interaction: Interaction,invite_url: str,role: Optional[Role]) -> Embed:
    if role:
        return error_response.embed(interaction,f"The invite **{invite_url}** is not connected to {role.mention}.")
    else:
        return error_response.embed(interaction,f"The invite **{invite_url}** is not connected to any roles.")