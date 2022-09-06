from discord import Color,Embed,Interaction
from . import base_response

def embed(interaction: Interaction,success_msg: str) -> Embed:
    embed: Embed = (
        base_response.embed(interaction)
        .set_footer(text="All changes saved!")
    )
    embed.color = Color.green()
    embed.title = "Success!"
    embed.description = success_msg
    return embed