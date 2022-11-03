from discord import Embed,Interaction
from . import error_response

def embed(interaction: Interaction) -> Embed:
    return error_response.embed(interaction,f"I need the **Create Invite** permission to perform this action.")