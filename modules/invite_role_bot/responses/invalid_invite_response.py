from discord import Embed,Interaction
from . import error_response

def embed(interaction: Interaction,invalid_invite: str) -> Embed:
    return error_response.embed(interaction,f"The invite **{invalid_invite}** is invalid or may be expired.")