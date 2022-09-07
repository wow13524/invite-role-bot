from discord import Embed,Interaction,Role
from typing import Optional
from . import success_response

def embed(interaction: Interaction,invite_url: str,role: Optional[Role]) -> Embed:
    if role:
        return success_response.embed(interaction,f"The invite **{invite_url}** is no longer connected to {role.mention}.")
    else:
        return success_response.embed(interaction,f"The invite **{invite_url}** is no longer connected to any roles.")