from discord import Embed,Interaction,Role
from . import error_response

def embed(interaction: Interaction,role: Role) -> Embed:
    return error_response.embed(interaction,f"The role {role.mention} cannot be assigned to other users.")