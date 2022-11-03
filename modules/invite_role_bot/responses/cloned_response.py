from discord import Embed,Interaction
from . import success_response

def embed(interaction: Interaction,invite_url: str) -> Embed:
    return success_response.embed(interaction,f"Your invite was successfully cloned.\nThe new invite URL is **{invite_url}**.")