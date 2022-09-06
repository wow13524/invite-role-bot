from datetime import datetime
from discord import Embed,Interaction

def embed(interaction: Interaction) -> Embed:
    assert interaction.guild
    return (
        Embed(timestamp=datetime.now())
        .set_author(name=interaction.guild.me.display_name,icon_url=interaction.guild.me.display_avatar.url)
    )