from discord import Color,Embed,Interaction
from . import base_response

def embed(interaction: Interaction,err_msg: str) -> Embed:
    embed: Embed = (
        base_response.embed(interaction)
        .set_footer(text="Oops, something went wrong!")
    )
    embed.color = Color.brand_red()
    embed.title = "Error!"
    embed.description = err_msg
    return embed