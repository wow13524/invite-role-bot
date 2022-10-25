from discord import ButtonStyle,Embed,Interaction
from discord.ui import Button,View
from typing import List,Literal,Optional,TypedDict

NavButtonType = Literal["⏪","◀️","▶️","⏩"]

EMBED_LIMIT: int = 5750
MAX_FIELDS: int = 8
NAV_FIRST: NavButtonType = "⏪"
NAV_BACK: NavButtonType = "◀️"
NAV_FORWARD: NavButtonType = "▶️"
NAV_LAST: NavButtonType = "⏩"

class EmbedField(TypedDict):
    name: str
    value: str
    inline: bool

class PaginationView(View):
    def __init__(self,*,embed: Embed,timeout: Optional[float]=180.0) -> None:
        super().__init__(timeout=timeout)
        self._embed: Embed = embed
        self._embed_proxy: Embed = embed.copy().clear_fields()
        self._fields: List[List[EmbedField]] = [[]]
        self._page: int = 0

        self._nav_button_first: Button[PaginationView] = NavButton(NAV_FIRST)
        self._nav_button_back: Button[PaginationView] = NavButton(NAV_BACK)
        self._nav_button_forward: Button[PaginationView] = NavButton(NAV_FORWARD)
        self._nav_button_last: Button[PaginationView] = NavButton(NAV_LAST)
    
    @property
    def page(self) -> int:
        return self._page

    def _update_buttons(self):
        if len(self._fields) == 1 and self.children:
            self.clear_items()
        elif len(self._fields) > 1 and not self.children:
            self.add_item(self._nav_button_first).add_item(self._nav_button_back).add_item(self._nav_button_forward).add_item(self._nav_button_last)
        self._nav_button_first.disabled = self._nav_button_back.disabled = self._page == 0
        self._nav_button_forward.disabled = self._nav_button_last.disabled = self._page == len(self._fields)-1

    def set_page(self,page: int) -> None:
        self._page = page%len(self._fields)
        self._embed.clear_fields()
        for field in self._fields[page]:
            self._embed.add_field(**field)
        self._embed.add_field(name="‍",value="‍",inline=False)  #bottom padding
        self._embed.set_footer(text=f"Page {self._page+1} of {len(self._fields)}")
        self._update_buttons()

    def add_field(self,*,name: str,value: str,inline: bool=True) -> None:
        self._embed_proxy.add_field(name=name,value=value,inline=inline)
        if len(self._fields[-1]) == MAX_FIELDS or len(self._embed_proxy) > EMBED_LIMIT:
            self._embed_proxy.clear_fields()
            self._embed_proxy.add_field(name=name,value=value,inline=inline)
            self._fields.append([])
        self._fields[-1].append({
            "name": name,
            "value": value,
            "inline": inline
        })
        self.set_page(self._page)
    
    async def update_interaction(self,interaction: Interaction) -> None:
        await interaction.response.edit_message(embed=self._embed,view=self)

class NavButton(Button[PaginationView]):
    def __init__(self,button_type: NavButtonType) -> None:
        super().__init__(style=ButtonStyle.primary,disabled=True,custom_id=button_type,emoji=button_type)
        self._type: NavButtonType = button_type
    
    async def callback(self,interaction: Interaction) -> None:
        assert self.view
        if self._type == NAV_FIRST:
            self.view.set_page(0)
        elif self._type == NAV_BACK:
            self.view.set_page(self.view.page-1)
        elif self._type == NAV_FORWARD:
            self.view.set_page(self.view.page+1)
        elif self._type == NAV_LAST:
            self.view.set_page(-1)
        await self.view.update_interaction(interaction)
        