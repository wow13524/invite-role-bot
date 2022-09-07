from discord import Embed,Interaction
from . import error_response

def embed(interaction: Interaction,invite_url: str) -> Embed:
    return error_response.embed(interaction,f"The invite **{invite_url}** belongs to a different guild.")