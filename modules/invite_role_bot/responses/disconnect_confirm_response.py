from discord import ButtonStyle,Color,Embed,Interaction
from discord.ui import Button,View
from typing import Any,Callable,Coroutine,Tuple
from . import base_response,success_response

EmbedCallback = Callable[[Interaction],Coroutine[Any,Any,Embed]]

class ConfirmationView(View):
    def __init__(self,*,timeout: float=180.0,style: ButtonStyle,label: str,callback_confirm: EmbedCallback) -> None:
        super().__init__(timeout=timeout)
        self.add_item(CancelButton())
        self.add_item(ConfirmButton(style=style,label=label,callback=callback_confirm))

class BaseConfirmationButton(Button[ConfirmationView]):
    def __init__(self,style: ButtonStyle,label: str,callback: EmbedCallback) -> None:
        super().__init__(style=style,label=label)
        self._callback = callback

    async def callback(self,interaction: Interaction) -> None:
        await interaction.response.edit_message(embed=await self._callback(interaction),view=None)

async def callback_cancel(interaction: Interaction) -> Embed:
    return success_response.embed(interaction,"Operation canceled.")

class CancelButton(BaseConfirmationButton):
    def __init__(self) -> None:
        super().__init__(style=ButtonStyle.gray,label="Cancel",callback=callback_cancel)

class ConfirmButton(BaseConfirmationButton):
    def __init__(self,style: ButtonStyle,label: str,callback: EmbedCallback) -> None:
        super().__init__(style=style,label=label,callback=callback)

def embed(interaction: Interaction,invite_url: str,num_roles: int,callback: EmbedCallback) -> Tuple[Embed,ConfirmationView]:
    assert interaction.guild
    embed: Embed = base_response.embed(interaction)
    embed.color = Color.brand_red()
    embed.title = f"Confirm Action:"
    embed.description = f"Are you sure you want to disconnect **{invite_url}** from **{num_roles}** role{'s' if num_roles > 1 else ''}?"
    confirmation_view: ConfirmationView = ConfirmationView(style=ButtonStyle.danger,label="Disconnect",callback_confirm=callback)
    return (embed,confirmation_view)